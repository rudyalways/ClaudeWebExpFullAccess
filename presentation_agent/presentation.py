"""
Top-level PresentationAgent.

Responsibilities:
1. Call Claude to plan the slide deck (titles, topics, layout hints)
2. Spawn one AgentTeam per slide, all running concurrently
3. Hand the collected slide HTML to the renderer to produce the final page

This is the entry-point for all user-facing usage.
"""

from __future__ import annotations

import asyncio
from typing import List

import anthropic

from .models import (
    PresentationBrief, PresentationPlan, SlideSpec,
    AreaSpec, Bounds,
)
from .agent import AgentTeam
from .renderer import assemble_presentation
from .prompts import SLIDE_PLAN_TOOL, SLIDE_PLANNER_SYSTEM, SLIDE_PLANNER_USER


class PresentationAgent:
    """
    Root orchestrator for the entire presentation generation pipeline.

    Usage::

        brief = PresentationBrief(
            title="AI in 2026",
            topic="State of artificial intelligence",
            description="...",
            slide_count=6,
        )
        html = await PresentationAgent().run(brief)
        with open("out.html", "w") as f:
            f.write(html)
    """

    def __init__(self, model: str = "claude-sonnet-4-6"):
        self.client = anthropic.AsyncAnthropic()
        self.model = model

    # ── Public API ────────────────────────────────────────────────────────────

    async def run(self, brief: PresentationBrief) -> str:
        """
        Generate a complete, self-contained HTML presentation.

        Pipeline:
          1. Plan slides  (1 Claude call)
          2. Generate each slide in parallel (recursive agent trees)
          3. Assemble final HTML (pure Python)
        """
        _banner(f"Presentation: {brief.title!r}")
        print(f"  Slides planned: {brief.slide_count}  |  Style: {brief.style.theme}")

        # ── Step 1: Plan the slide structure ──────────────────────────────
        plan = await self._plan_slides(brief)
        print(f"\n  Planned {len(plan.slides)} slides:")
        for s in plan.slides:
            print(f"    [{s.index+1}] {s.title!r}  ({s.layout_hint})")

        # ── Step 2: Generate all slides concurrently ──────────────────────
        print()
        slide_htmls: List[str] = list(
            await asyncio.gather(*[
                self._generate_slide(slide, brief)
                for slide in plan.slides
            ])
        )

        # ── Step 3: Assemble the final HTML page ──────────────────────────
        html = assemble_presentation(brief, plan.slides, slide_htmls)
        _banner(f"Done — {len(plan.slides)} slides, {len(html):,} chars")
        return html

    # ── Private helpers ────────────────────────────────────────────────────

    async def _plan_slides(self, brief: PresentationBrief) -> PresentationPlan:
        """Ask Claude to create the slide structure."""
        prompt = SLIDE_PLANNER_USER.format(
            count=brief.slide_count,
            title=brief.title,
            topic=brief.topic,
            description=brief.description,
            audience=brief.audience,
            style=brief.style_preferences,
        )

        resp = await self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            system=SLIDE_PLANNER_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            tools=[SLIDE_PLAN_TOOL],
            tool_choice={"type": "any"},
        )

        for block in resp.content:
            if block.type == "tool_use" and block.name == "plan_presentation":
                raw_slides = block.input.get("slides", [])
                slides = [
                    SlideSpec(
                        index=i,
                        title=s.get("title", f"Slide {i+1}"),
                        topic=s.get("topic", ""),
                        description=s.get("description", ""),
                        layout_hint=s.get("layout_hint", "auto"),
                    )
                    for i, s in enumerate(raw_slides)
                ]
                return PresentationPlan(title=brief.title, slides=slides)

        # Fallback: single slide
        return PresentationPlan(
            title=brief.title,
            slides=[
                SlideSpec(
                    index=0,
                    title=brief.title,
                    topic=brief.topic,
                    description=brief.description,
                    layout_hint="content-left-visual-right",
                )
            ],
        )

    async def _generate_slide(
        self, slide: SlideSpec, brief: PresentationBrief
    ) -> str:
        """
        Generate one slide's HTML by running the full recursive agent tree.

        The root AgentTeam receives a 100×100 AreaSpec representing the entire
        slide canvas.  It recursively subdivides and generates content.
        """
        print(f"  === Slide {slide.index+1}: {slide.title!r} ===")

        root_spec = AreaSpec(
            id=f"s{slide.index}",
            topic=slide.title,
            description=(
                f"{slide.description}  "
                f"[Layout hint: {slide.layout_hint}]"
            ),
            bounds=Bounds.full(),
            depth=0,
            parent_context=(
                f"Slide {slide.index+1} of {len([slide])+brief.slide_count-1} "
                f"in '{brief.title}'"
            ),
            style=brief.style,
            slide_title=slide.title,
            content_hint="auto",
        )

        team = AgentTeam(self.client)
        result = await team.execute(root_spec)
        return result.content


# ─── Utility ──────────────────────────────────────────────────────────────────

def _banner(msg: str) -> None:
    line = "─" * min(len(msg) + 4, 60)
    print(f"\n{line}")
    print(f"  {msg}")
    print(f"{line}")
