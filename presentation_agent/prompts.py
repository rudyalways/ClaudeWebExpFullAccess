"""
Prompt templates and tool schemas for each agent role.

Agent roles:
  PlannerAgent  — decides whether to subdivide an area or generate leaf content
  ContentAgent  — generates the actual HTML/SVG for a leaf area
  SlideAgent    — plans the full slide structure from a brief
"""

# ─── Tool schemas (Anthropic tool_use format) ─────────────────────────────────

PLAN_TOOL = {
    "name": "plan_area",
    "description": (
        "Decide whether this area should subdivide into sub-areas (orchestrate) "
        "or generate content directly (leaf). Return structured JSON."
    ),
    "input_schema": {
        "type": "object",
        "required": ["is_leaf", "reasoning"],
        "properties": {
            "is_leaf": {
                "type": "boolean",
                "description": "True → generate content here. False → subdivide into children.",
            },
            "reasoning": {
                "type": "string",
                "description": "One-sentence explanation of the decision.",
            },
            "children": {
                "type": "array",
                "description": (
                    "Required when is_leaf=false. "
                    "2–9 sub-areas tiling the parent space. "
                    "Coordinates are 0–100 % *within* the parent area."
                ),
                "minItems": 2,
                "maxItems": 9,
                "items": {
                    "type": "object",
                    "required": ["topic", "description", "x", "y", "width", "height"],
                    "properties": {
                        "topic": {"type": "string"},
                        "description": {"type": "string"},
                        "x": {"type": "number", "minimum": 0, "maximum": 100},
                        "y": {"type": "number", "minimum": 0, "maximum": 100},
                        "width": {"type": "number", "minimum": 1, "maximum": 100},
                        "height": {"type": "number", "minimum": 1, "maximum": 100},
                        "content_hint": {
                            "type": "string",
                            "enum": [
                                "auto", "title", "text", "bullets",
                                "chart", "diagram", "code",
                                "image", "icon", "quote",
                                "background", "decorative",
                            ],
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["html", "svg"],
                        },
                    },
                },
            },
        },
    },
}

CONTENT_TOOL = {
    "name": "generate_content",
    "description": "Generate self-contained HTML or inline SVG content for this area.",
    "input_schema": {
        "type": "object",
        "required": ["content", "format"],
        "properties": {
            "content": {
                "type": "string",
                "description": (
                    "The complete, self-contained HTML fragment or inline SVG string. "
                    "No <html>/<head>/<body> tags. Use only inline styles."
                ),
            },
            "format": {
                "type": "string",
                "enum": ["html", "svg"],
            },
        },
    },
}

SLIDE_PLAN_TOOL = {
    "name": "plan_presentation",
    "description": "Create the complete slide plan for the presentation.",
    "input_schema": {
        "type": "object",
        "required": ["slides"],
        "properties": {
            "slides": {
                "type": "array",
                "minItems": 1,
                "maxItems": 20,
                "items": {
                    "type": "object",
                    "required": ["title", "topic", "description"],
                    "properties": {
                        "title": {"type": "string"},
                        "topic": {"type": "string"},
                        "description": {
                            "type": "string",
                            "description": "Rich description of what this slide should show visually.",
                        },
                        "layout_hint": {
                            "type": "string",
                            "enum": [
                                "title-hero",
                                "content-left-visual-right",
                                "visual-left-content-right",
                                "full-visual",
                                "grid-2x2",
                                "grid-3-cols",
                                "text-heavy",
                                "data-visualization",
                                "quote-highlight",
                                "timeline",
                                "comparison",
                                "closing",
                            ],
                        },
                    },
                },
            },
        },
    },
}

# ─── System prompts ────────────────────────────────────────────────────────────

PLANNER_SYSTEM = """\
You are a visual presentation layout expert. Your role is to analyze a content area
within a slide and decide how to structure it visually.

Decision rules:
- depth ≥ 3 → strong preference for leaf (generate content directly)
- depth = 0 or 1 → typically orchestrate (subdivide into logical regions)
- depth = 2 → either, based on complexity
- Simple/atomic content → leaf (single chart, heading, bullet list, decorative element)
- Complex content with multiple distinct parts → orchestrate (e.g. hero area = background + title + subtitle + CTA)

When subdividing:
- Plan 2–9 children that cover the space meaningfully
- Use % coordinates (0–100) *within the parent* (not absolute)
- Children may have small gaps for visual breathing room
- Apply visual hierarchy: dominant area + supporting areas
- Mix content types: text + visuals, not all text

Layout patterns to consider:
- Header (10% height) + Body (80%) + Footer (10%)
- Left panel (40%) + Right panel (60%)
- 3-column grid (each ~33%)
- Hero (60%) + 2 supporting cards below (each 50% width)
- Full-width header + 2x3 icon grid body
"""

PLANNER_USER = """\
Analyze this area and decide: subdivide into sub-areas, or generate as leaf content?

Area:
  ID: {id}
  Topic: "{topic}"
  Description: "{description}"
  Depth: {depth} / 4 (max)
  Parent context: "{parent_context}"
  Slide title: "{slide_title}"
  Content hint: {content_hint}

Call plan_area with your decision.\
"""

CONTENT_SYSTEM = """\
You are an expert presentation designer. Generate beautiful, professional HTML or SVG
content for a single visual area within a presentation slide.

Requirements:
- Output ONLY the inner content (no <html>, <head>, <body> wrapper tags)
- Use only INLINE styles (no <style> blocks, no external CSS)
- The content fills a container div with position:relative; width:100%; height:100%
- For SVG: output a complete <svg viewBox="0 0 100 100"> with preserveAspectRatio
- Be visually impressive: gradients, shapes, typography hierarchy, color harmony
- Match the provided color theme exactly
- No external dependencies (no CDN links, no Google Fonts in the output)
- Content should be meaningful and specific — not placeholder lorem ipsum
- For charts: use SVG path/rect/circle elements with real-looking data

Content guidelines by type:
  title       → Large headline, optional subtitle, perhaps a gradient text effect
  bullets     → Clean list with colored bullets/icons, good line-height
  chart       → SVG bar/line/pie chart with labeled axes and realistic values
  diagram     → SVG flowchart, architecture diagram, or concept map
  code        → Styled code block with syntax-colored spans
  quote       → Large quote with attribution, decorative quotation marks
  image       → SVG illustration or abstract graphic representing the topic
  background  → Full-area gradient or pattern as a decorative layer
  decorative  → Abstract shapes, particles, geometric pattern
  icon        → Large centered SVG icon + label
  text        → Paragraph with good typography
"""

CONTENT_USER = """\
Generate content for this presentation area:

  Topic: "{topic}"
  Description: "{description}"
  Content type hint: {content_hint}
  Output format: {output_format}

Theme:
  Background: {bg}
  Primary: {primary}
  Secondary: {secondary}
  Text: {text}
  Accent: {accent}
  Font: {font}

Context:
  Slide: "{slide_title}"
  Parent: "{parent_context}"

Generate visually impressive, professional content. Call generate_content.\
"""

SLIDE_PLANNER_SYSTEM = """\
You are a presentation architect. Given a brief, design a compelling slide deck
with strong narrative flow, visual variety, and clear information hierarchy.

Design principles:
- Open with an impactful hero/title slide
- Vary layouts: don't repeat the same structure twice in a row
- Mix text, data visualizations, and visuals
- Close with a strong summary or call-to-action
- Each slide's description should be rich enough for a visual AI to render it fully

Available layout hints:
  title-hero                 — Full-screen headline with background
  content-left-visual-right  — Text on left, chart/image on right
  visual-left-content-right  — Visual on left, text on right
  full-visual                — Mostly/fully visual (chart, infographic, photo)
  grid-2x2                   — Four equal quadrants
  grid-3-cols                — Three columns
  text-heavy                 — Long-form text with structure
  data-visualization         — Chart or data graphic as focal point
  quote-highlight            — Large pull-quote centered
  timeline                   — Horizontal or vertical timeline
  comparison                 — Side-by-side comparison
  closing                    — Summary, CTA, or thank-you
"""

SLIDE_PLANNER_USER = """\
Create a {count}-slide presentation:

  Title: "{title}"
  Topic: "{topic}"
  Description: "{description}"
  Audience: {audience}
  Style preferences: {style}

Design {count} slides with a clear narrative arc. Make each description vivid
so downstream agents can render beautiful visuals. Call plan_presentation.\
"""
