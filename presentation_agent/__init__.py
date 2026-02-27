"""
Presentation Agent - Recursive AI agent system for generating beautiful HTML presentations.

Architecture:
  PresentationAgent (root)
  └── RecursiveAgentTeam (per slide, depth=0)
      └── OrchestratorAgent → 2-9 RegionTeams (depth=1)
          └── OrchestratorAgent → 2-9 SubRegionTeams (depth=2)
              └── OrchestratorAgent → 2-9 SubAreas (depth=3)
                  └── LeafAgent → HTML/SVG content (depth=4, max)

Each level has an agent TEAM:
  - PlannerAgent  : decides to subdivide or generate
  - ContentAgent  : generates leaf HTML/SVG
  - ComposerAgent : assembles children via CSS positioning
"""

from .models import PresentationBrief, StyleContext, MAX_DEPTH
from .presentation import PresentationAgent

__all__ = ["PresentationBrief", "StyleContext", "PresentationAgent", "MAX_DEPTH"]
