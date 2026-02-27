"""
Core recursive agent implementation.

Architecture
============

Each node in the agent tree is an AgentTeam consisting of three roles:

  PlannerAgent   → Calls Claude to decide: subdivide OR generate leaf
  ContentAgent   → Calls Claude to generate HTML/SVG content (leaf only)
  ComposerAgent  → Pure Python: assembles children via CSS absolute positioning

The tree recurses until depth == MAX_DEPTH, where all nodes are forced to be leaves.

                  AgentTeam (depth=0)  ← slide root
                 /         |         \
         AgentTeam      AgentTeam   AgentTeam   (depth=1)
         /     \          |
   AgentTeam  Leaf   AgentTeam               (depth=2)
       |               /    \
      Leaf           Leaf   Leaf             (depth=3 or 4 forced leaf)

Parallelism
===========
Children at each level are executed with asyncio.gather(), so all sub-agents
within a level run concurrently (limited by the Anthropic API rate limits).
"""

from __future__ import annotations

import asyncio
import textwrap
from typing import List

import anthropic

from .models import (
    AreaSpec, AgentResult, Bounds,
    ChildAreaPlan, PlanResult,
    MAX_DEPTH,
)
from .prompts import (
    PLAN_TOOL, CONTENT_TOOL,
    PLANNER_SYSTEM, PLANNER_USER,
    CONTENT_SYSTEM, CONTENT_USER,
)

# ─── Model config ─────────────────────────────────────────────────────────────

ORCHESTRATOR_MODEL = "claude-sonnet-4-6"   # Used for planning decisions
LEAF_MODEL = "claude-sonnet-4-6"           # Used for content generation

# ─── Individual agent roles ───────────────────────────────────────────────────

class PlannerAgent:
    """
    Role: Decide whether to subdivide this area into 2–9 children or generate
    content as a leaf.  Always a single Claude call with structured tool use.
    """

    def __init__(self, client: anthropic.AsyncAnthropic, model: str = ORCHESTRATOR_MODEL):
        self.client = client
        self.model = model

    async def plan(self, spec: AreaSpec) -> PlanResult:
        prompt = PLANNER_USER.format(
            id=spec.id,
            topic=spec.topic,
            description=spec.description,
            depth=spec.depth,
            parent_context=spec.parent_context or "none",
            slide_title=spec.slide_title,
            content_hint=spec.content_hint,
        )

        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            system=PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            tools=[PLAN_TOOL],
            tool_choice={"type": "any"},
        )

        for block in resp.content:
            if block.type == "tool_use" and block.name == "plan_area":
                data = block.input
                children = [
                    ChildAreaPlan(**c) for c in data.get("children", [])
                ]
                return PlanResult(
                    is_leaf=data.get("is_leaf", True),
                    reasoning=data.get("reasoning", ""),
                    children=children,
                )

        # Fallback: treat as leaf
        return PlanResult(is_leaf=True, reasoning="API fallback → leaf")


class ContentAgent:
    """
    Role: Generate self-contained HTML or SVG for a leaf area.
    Uses Claude with tool_use for reliable structured output.
    """

    def __init__(self, client: anthropic.AsyncAnthropic, model: str = LEAF_MODEL):
        self.client = client
        self.model = model

    async def generate(self, spec: AreaSpec) -> AgentResult:
        s = spec.style
        prompt = CONTENT_USER.format(
            topic=spec.topic,
            description=spec.description,
            content_hint=spec.content_hint,
            output_format="svg" if spec.content_hint in ("background", "decorative", "chart", "diagram", "icon") else "html",
            bg=s.background_color,
            primary=s.primary_color,
            secondary=s.secondary_color,
            text=s.text_color,
            accent=s.accent_color,
            font=s.font_family,
            slide_title=spec.slide_title,
            parent_context=spec.parent_context or "none",
        )

        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=CONTENT_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            tools=[CONTENT_TOOL],
            tool_choice={"type": "any"},
        )

        content = ""
        fmt = "html"
        for block in resp.content:
            if block.type == "tool_use" and block.name == "generate_content":
                content = block.input.get("content", "")
                fmt = block.input.get("format", "html")
                break

        if not content:
            # Minimal fallback so the tree still composes
            content = _fallback_content(spec)
            fmt = "html"

        return AgentResult(
            id=spec.id,
            content=content,
            format=fmt,  # type: ignore[arg-type]
            bounds=spec.bounds,
            depth=spec.depth,
            metadata={"topic": spec.topic},
        )


class ComposerAgent:
    """
    Role: Assemble a list of child AgentResults into a single parent container.
    Pure Python — no LLM call needed.  Children are positioned using CSS
    absolute layout with percentage-based coordinates.
    """

    def compose(self, spec: AreaSpec, children: List[AgentResult]) -> AgentResult:
        parts: List[str] = []
        for child in children:
            b = child.bounds
            style = (
                f"position:absolute;"
                f"left:{b.x:.2f}%;top:{b.y:.2f}%;"
                f"width:{b.width:.2f}%;height:{b.height:.2f}%;"
                f"overflow:hidden;"
            )
            parts.append(f'<div style="{style}">{child.content}</div>')

        composed = (
            '<div style="position:relative;width:100%;height:100%;">'
            + "".join(parts)
            + "</div>"
        )

        return AgentResult(
            id=spec.id,
            content=composed,
            format="html",
            bounds=spec.bounds,
            depth=spec.depth,
            metadata={"children": len(children)},
        )

# ─── Agent team ───────────────────────────────────────────────────────────────

class AgentTeam:
    """
    One node in the recursive agent tree.

    Team members:
      planner  → PlannerAgent (Claude call)
      content  → ContentAgent (Claude call, only at leaves)
      composer → ComposerAgent (pure Python, only at orchestrators)

    The team is re-instantiated for each node (stateless by design).
    """

    def __init__(self, client: anthropic.AsyncAnthropic):
        self.client = client
        self.planner = PlannerAgent(client)
        self.content = ContentAgent(client)
        self.composer = ComposerAgent()

    async def execute(self, spec: AreaSpec) -> AgentResult:
        indent = "  " * spec.depth
        print(f"{indent}[d={spec.depth}] team={spec.id!r} topic={spec.topic!r}")

        # ── Force leaf at maximum depth ────────────────────────────────────
        if spec.depth >= MAX_DEPTH:
            print(f"{indent}  → max depth reached, generating leaf")
            return await self.content.generate(spec)

        # ── Ask the planner ────────────────────────────────────────────────
        plan = await self.planner.plan(spec)
        print(f"{indent}  planner → is_leaf={plan.is_leaf} | {plan.reasoning[:60]}")

        if plan.is_leaf or not plan.children:
            return await self.content.generate(spec)

        # ── Spawn child teams in parallel ──────────────────────────────────
        child_specs = [
            _child_plan_to_spec(spec, idx, child)
            for idx, child in enumerate(plan.children)
        ]
        print(f"{indent}  → spawning {len(child_specs)} child teams")

        child_results = await asyncio.gather(*[
            AgentTeam(self.client).execute(cs)
            for cs in child_specs
        ])

        # ── Composer assembles the results ─────────────────────────────────
        return self.composer.compose(spec, list(child_results))

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _child_plan_to_spec(parent: AreaSpec, index: int, child: ChildAreaPlan) -> AreaSpec:
    """Convert a ChildAreaPlan into a full AreaSpec for the child team."""
    return AreaSpec(
        id=f"{parent.id}-{index}",
        topic=child.topic,
        description=child.description,
        bounds=Bounds(
            x=child.x,
            y=child.y,
            width=child.width,
            height=child.height,
        ),
        depth=parent.depth + 1,
        parent_context=(
            f"Inside '{parent.topic}': {textwrap.shorten(parent.description, width=120)}"
        ),
        style=parent.style,
        slide_title=parent.slide_title,
        content_hint=child.content_hint,  # type: ignore[arg-type]
    )


def _fallback_content(spec: AreaSpec) -> str:
    """Minimal placeholder when Claude produces no tool call."""
    s = spec.style
    return (
        f'<div style="'
        f"display:flex;align-items:center;justify-content:center;"
        f"width:100%;height:100%;"
        f"color:{s.text_color};font-family:{s.font_family};"
        f"font-size:14px;opacity:0.4;"
        f'">'
        f"{spec.topic}"
        f"</div>"
    )
