# CLAUDE.md

This file provides guidance for AI assistants (Claude Code and similar tools) working in this repository.

## Repository Overview

**Name:** ClaudeWebExpFullAccess
**Purpose:** A repository configured for full-access Claude Code on the web sessions.

This is a fresh repository — no application code exists yet. As the project evolves, update this file to reflect the actual codebase structure, tech stack, and conventions.

---

## Repository Structure

```
.
├── CLAUDE.md                  # This file — AI assistant guidance
├── .claude/
│   ├── settings.json          # Claude Code configuration (hooks, permissions)
│   └── hooks/
│       └── session-start.sh   # SessionStart hook: installs dependencies on session start
└── (source code to be added)
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

## Adding a Tech Stack

When you add code to this repository, update this file with:

1. **Tech stack:** Language, framework, runtime version
2. **Install command:** How to install dependencies
3. **Run command:** How to start the dev server / application
4. **Test command:** How to run the test suite
5. **Lint command:** How to run linters / formatters
6. **Build command:** How to produce a production build

Example (Node.js/TypeScript project):

```bash
# Install
npm install

# Dev server
npm run dev

# Tests
npm test

# Lint
npm run lint

# Build
npm run build
```

---

## Key Conventions (to be filled in)

As development begins, document decisions here:

- **Code style:** (e.g., Prettier + ESLint, Black + Ruff, rustfmt)
- **Testing framework:** (e.g., Jest, pytest, cargo test)
- **Environment variables:** List required env vars and their purpose
- **Database / storage:** Connection patterns, migration workflow
- **API conventions:** REST/GraphQL patterns, error format, auth method

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
