#!/usr/bin/env python3
"""
Presentation Agent — CLI entry point.

Usage examples
--------------
# Built-in demo
python main.py --example

# Custom brief (short form)
python main.py --title "The Future of AI" --slides 5

# Full brief
python main.py \\
  --title "Quantum Computing in Finance" \\
  --topic "Quantum algorithms for portfolio optimisation" \\
  --description "A deep-dive for CFOs and quant teams covering QPUs, ..." \\
  --audience "Finance professionals" \\
  --slides 7 \\
  --style modern-dark \\
  --output my_deck.html

Themes: modern-dark | modern-light | corporate | minimal | neon | nature
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running from repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent))

from presentation_agent.models import PresentationBrief, StyleContext
from presentation_agent.presentation import PresentationAgent

# ─── Built-in style presets ───────────────────────────────────────────────────

STYLE_PRESETS: dict[str, StyleContext] = {
    "modern-dark": StyleContext(
        theme="modern-dark",
        primary_color="#6366f1",
        secondary_color="#a855f7",
        background_color="#0a0a1a",
        text_color="#e2e8f0",
        accent_color="#22d3ee",
        font_family="'Inter', system-ui, sans-serif",
    ),
    "modern-light": StyleContext(
        theme="modern-light",
        primary_color="#4f46e5",
        secondary_color="#7c3aed",
        background_color="#f8fafc",
        text_color="#0f172a",
        accent_color="#0ea5e9",
        font_family="'Inter', system-ui, sans-serif",
    ),
    "corporate": StyleContext(
        theme="corporate",
        primary_color="#1e40af",
        secondary_color="#1d4ed8",
        background_color="#ffffff",
        text_color="#111827",
        accent_color="#3b82f6",
        font_family="'Georgia', serif",
    ),
    "minimal": StyleContext(
        theme="minimal",
        primary_color="#18181b",
        secondary_color="#3f3f46",
        background_color="#fafafa",
        text_color="#18181b",
        accent_color="#71717a",
        font_family="'Helvetica Neue', Arial, sans-serif",
    ),
    "neon": StyleContext(
        theme="neon",
        primary_color="#00ff88",
        secondary_color="#ff00ff",
        background_color="#000000",
        text_color="#ffffff",
        accent_color="#ffff00",
        font_family="'Courier New', monospace",
    ),
    "nature": StyleContext(
        theme="nature",
        primary_color="#2d7d46",
        secondary_color="#56b870",
        background_color="#f0f7f0",
        text_color="#1a3a1a",
        accent_color="#e67e22",
        font_family="'Georgia', serif",
    ),
}

# ─── Example brief ────────────────────────────────────────────────────────────

EXAMPLE_BRIEF = PresentationBrief(
    title="The Future of AI-Powered Development",
    topic="Artificial intelligence transforming software engineering",
    description="""
    An exploration of how AI is reshaping the software development lifecycle —
    from intelligent code completion and automated testing to AI-driven architecture
    decisions and autonomous debugging agents. Include compelling statistics,
    real-world tool comparisons, productivity data, architectural diagrams,
    and a forward-looking roadmap for AI-augmented engineering teams.
    Make it visually rich with charts showing developer productivity gains,
    a timeline of key milestones, and a comparison of traditional vs AI-assisted workflows.
    """,
    audience="software engineers, tech leads, and CTOs",
    style_preferences="modern, data-driven, visually rich with charts and diagrams",
    slide_count=7,
    style=STYLE_PRESETS["modern-dark"],
)

# ─── Main ─────────────────────────────────────────────────────────────────────

async def generate(brief: PresentationBrief, output: str) -> None:
    agent = PresentationAgent()
    html = await agent.run(brief)

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")

    print(f"\n  Output saved → {out_path.resolve()}")
    print(f"  Open in browser: file://{out_path.resolve()}\n")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a beautiful HTML presentation using recursive AI agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--title",       default="", help="Presentation title")
    p.add_argument("--topic",       default="", help="Main topic (defaults to title)")
    p.add_argument("--description", default="", help="Detailed description / brief")
    p.add_argument("--audience",    default="general", help="Target audience")
    p.add_argument("--slides",      type=int, default=5, metavar="N", help="Number of slides (1–20)")
    p.add_argument(
        "--style",
        default="modern-dark",
        choices=list(STYLE_PRESETS.keys()),
        help="Visual theme preset",
    )
    p.add_argument("--output", default="presentation.html", help="Output HTML file path")
    p.add_argument("--example", action="store_true", help="Run the built-in demo brief")
    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.example or not args.title:
        brief = EXAMPLE_BRIEF
    else:
        brief = PresentationBrief(
            title=args.title,
            topic=args.topic or args.title,
            description=args.description or args.title,
            audience=args.audience,
            slide_count=max(1, min(20, args.slides)),
            style_preferences=f"{args.style} theme",
            style=STYLE_PRESETS.get(args.style, STYLE_PRESETS["modern-dark"]),
        )

    asyncio.run(generate(brief, args.output))


if __name__ == "__main__":
    main()
