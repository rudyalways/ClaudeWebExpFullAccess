"""
Data models for the presentation agent system.

All coordinates are percentage-based (0-100) relative to the parent container,
enabling recursive CSS positioning without absolute pixel values.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import List, Literal, Dict, Any, Optional

# ─── Constants ────────────────────────────────────────────────────────────────

MAX_DEPTH = 4        # Maximum recursion depth (leaf forced at this depth)
MIN_CHILDREN = 2     # Minimum sub-areas when orchestrating
MAX_CHILDREN = 9     # Maximum sub-areas when orchestrating

# ─── Style ────────────────────────────────────────────────────────────────────

class StyleContext(BaseModel):
    """Visual style context — inherited down the agent tree."""

    theme: str = "modern-dark"
    primary_color: str = "#6366f1"
    secondary_color: str = "#a855f7"
    background_color: str = "#0a0a1a"
    text_color: str = "#e2e8f0"
    accent_color: str = "#22d3ee"
    font_family: str = "'Inter', system-ui, sans-serif"
    # Optional per-agent overrides that children can inherit
    extra: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def light(cls) -> "StyleContext":
        return cls(
            theme="modern-light",
            primary_color="#4f46e5",
            secondary_color="#7c3aed",
            background_color="#f8fafc",
            text_color="#0f172a",
            accent_color="#0ea5e9",
        )

    @classmethod
    def corporate(cls) -> "StyleContext":
        return cls(
            theme="corporate",
            primary_color="#1e40af",
            secondary_color="#1d4ed8",
            background_color="#ffffff",
            text_color="#111827",
            accent_color="#3b82f6",
        )

# ─── Area geometry ────────────────────────────────────────────────────────────

class Bounds(BaseModel):
    """Percentage-based bounds within the parent container (0–100)."""

    x: float = Field(default=0.0, ge=0, le=100)
    y: float = Field(default=0.0, ge=0, le=100)
    width: float = Field(default=100.0, gt=0, le=100)
    height: float = Field(default=100.0, gt=0, le=100)

    @classmethod
    def full(cls) -> "Bounds":
        return cls(x=0, y=0, width=100, height=100)

# ─── Agent I/O ────────────────────────────────────────────────────────────────

class AreaSpec(BaseModel):
    """
    Input specification handed to every agent (or agent team).

    The id encodes the tree path, e.g. "s2-r1-sr3-0" for
    slide 2 → region 1 → sub-region 3 → child 0.
    """

    id: str
    topic: str
    description: str
    bounds: Bounds = Field(default_factory=Bounds.full)
    depth: int = 0
    parent_context: str = ""
    style: StyleContext = Field(default_factory=StyleContext)
    slide_title: str = ""
    # Hint about preferred content type (can be overridden by agent)
    content_hint: Literal[
        "auto",
        "title", "text", "bullets",
        "chart", "diagram", "code",
        "image", "icon", "quote",
        "background", "decorative",
    ] = "auto"

class ChildAreaPlan(BaseModel):
    """A child area as planned by the PlannerAgent."""

    topic: str
    description: str
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(gt=0, le=100)
    height: float = Field(gt=0, le=100)
    content_hint: str = "auto"
    output_format: Literal["html", "svg"] = "html"

class PlanResult(BaseModel):
    """Result from the PlannerAgent."""

    is_leaf: bool
    reasoning: str
    children: List[ChildAreaPlan] = Field(default_factory=list)

class AgentResult(BaseModel):
    """Output from any agent — embeddable HTML or SVG string."""

    id: str
    content: str           # Self-contained HTML or inline SVG
    format: Literal["html", "svg"] = "html"
    bounds: Bounds         # Position within parent (used by Composer)
    depth: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

# ─── Presentation planning ────────────────────────────────────────────────────

class SlideSpec(BaseModel):
    """Specification for a single slide."""

    index: int
    title: str
    topic: str
    description: str
    layout_hint: str = "auto"   # e.g. "title-only", "content-visual", "grid"

class PresentationPlan(BaseModel):
    """Full slide plan produced by PresentationAgent."""

    title: str
    slides: List[SlideSpec]

class PresentationBrief(BaseModel):
    """
    Top-level brief — the only input the user needs to provide.

    Example::

        brief = PresentationBrief(
            title="The Future of AI",
            topic="AI in software engineering",
            description="...",
            slide_count=6,
        )
        html = await PresentationAgent().run(brief)
    """

    title: str
    topic: str
    description: str
    audience: str = "general"
    style_preferences: str = "modern, professional, visually rich"
    slide_count: int = Field(default=5, ge=1, le=20)
    style: StyleContext = Field(default_factory=StyleContext)
