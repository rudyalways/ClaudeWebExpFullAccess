# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and similar tools) working in this repository.

## Repository Overview

**Name:** ClaudeWebExpFullAccess
**Purpose:** A repository configured for full-access Claude Code on the web sessions.

This repository contains the **Presentation Agent** — a recursive multi-agent system that generates beautiful HTML presentations (like PowerPoint) using Claude.

---

## Repository Structure

```
.
├── CLAUDE.md                        # This file — AI assistant guidance
├── main.py                          # CLI entry point
├── requirements.txt                 # Python dependencies
├── presentation_agent/              # Core Python package
│   ├── __init__.py                  # Package exports
│   ├── models.py                    # Pydantic data models (AreaSpec, AgentResult, …)
│   ├── prompts.py                   # Prompt templates + Anthropic tool schemas
│   ├── agent.py                     # Recursive AgentTeam (PlannerAgent + ContentAgent + ComposerAgent)
│   ├── presentation.py              # Top-level PresentationAgent orchestrator
│   └── renderer.py                  # Pure-Python HTML assembler
├── .claude/
│   ├── settings.json                # Claude Code configuration (hooks, permissions)
│   └── hooks/
│       └── session-start.sh         # SessionStart hook: installs dependencies on session start
└── (future: tests/, examples/, docs/)
```

---

## Development Workflow

### Branching

- **Main branch:** `main` (or `master` — update once established)
- **Feature branches:** `feature/<short-description>`
- **Bug fixes:** `fix/<short-description>`
- **Claude Code branches:** `claude/<task-id>` (auto-created by Claude Code web sessions)

### Commit Messages

Use the conventional commits format:

```
<type>(<scope>): <short summary>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(auth): add JWT token validation
fix(api): handle null response from upstream service
docs: update CLAUDE.md with API conventions
```

### Pull Requests

- Keep PRs focused — one concern per PR
- Include a description of what changed and why
- Link related issues

---

## Claude Code Configuration

### SessionStart Hook

A `SessionStart` hook is configured in `.claude/settings.json`. It runs `.claude/hooks/session-start.sh` at the beginning of every Claude Code web session to install dependencies and prepare the environment.

**To extend the hook** as the project grows, edit `.claude/hooks/session-start.sh` and add the appropriate install commands (e.g., `npm install`, `pip install -r requirements.txt`, `cargo build`).

### Settings

`.claude/settings.json` controls Claude Code behavior for this repository. It currently registers the SessionStart hook. Add additional permissions or tool configurations here as needed.

---

## Tech Stack

- **Language:** Python 3.11+
- **LLM provider:** Anthropic Claude (`claude-sonnet-4-6`) via `anthropic` Python SDK
- **Data validation:** Pydantic v2
- **Concurrency:** `asyncio` + `asyncio.gather` for parallel agent execution

```bash
# Install
pip install -r requirements.txt

# Generate a demo presentation (needs ANTHROPIC_API_KEY)
python main.py --example

# Custom brief
python main.py --title "My Talk" --slides 5 --style modern-dark --output out.html

# Open result
open out.html   # macOS
xdg-open out.html  # Linux
```

---

## Agent Architecture

The system is a **recursive multi-agent tree** (max depth 4):

```
PresentationAgent (root)
└── SlideSpec × N  ─────────── one Claude call plans all slides
    └── AgentTeam (depth=0)   ─ one team per slide, all run in parallel
        ├── PlannerAgent      ─ Claude call: subdivide vs. leaf?
        ├── AgentTeam × 2-9   ─ child teams, all run in parallel (depth=1)
        │   ├── PlannerAgent
        │   ├── AgentTeam × 2-9  (depth=2)
        │   │   └── …            (depth=3 → strong leaf preference)
        │   │       └── LeafAgent (depth=4, always leaf)
        │   └── ComposerAgent  ─ pure Python, CSS absolute positioning
        └── ComposerAgent
```

**Agent roles:**
- `PlannerAgent` — Calls Claude (tool_use) to decide: orchestrate or leaf?
- `ContentAgent` — Calls Claude (tool_use) to generate inline HTML/SVG
- `ComposerAgent` — Pure Python: wraps children in `position:absolute` divs

**Output format:** Each agent returns embeddable HTML or inline SVG. Parents
compose children with CSS percentage-based absolute positioning.

---

## Key Conventions

- **Code style:** PEP 8, type hints throughout, Pydantic models for all data
- **Async:** All agent methods are `async def`; use `asyncio.gather` for parallelism
- **Tool use:** Claude structured outputs via Anthropic tool_use (never raw JSON parsing)
- **Environment variables:**
  - `ANTHROPIC_API_KEY` — required (set in shell or `.env` not committed)
- **No external CSS/fonts** in generated slides — fully self-contained HTML output

---

## Working in Claude Code on the Web

This repository is optimized for [Claude Code on the web](https://claude.ai/code) full-access sessions.

### Useful reminders for AI assistants

- The `SessionStart` hook runs on every new session — dependencies should be installed automatically.
- The working directory is the repository root (`$CLAUDE_PROJECT_DIR`).
- Environment variables set via `$CLAUDE_ENV_FILE` persist for the session.
- The container state is cached after the hook completes — prefer install commands that benefit from layer caching (e.g., `npm install` over `npm ci`).
- When in doubt about project conventions, check this file first, then look at existing code patterns.
- Do not push directly to `main`/`master`. Use feature branches and PRs.
- Do not commit secrets, `.env` files, or credentials.

---

## Updating This File

Keep this file current as the project evolves:

- Update the **Repository Structure** section when new top-level directories are added.
- Update the **Tech Stack** section when dependencies change.
- Update **Key Conventions** when team decisions are made.
- Update the **SessionStart hook** section if the hook script changes.

Last updated: 2026-02-27
