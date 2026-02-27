#!/bin/bash
# SessionStart hook for Claude Code on the web
# Runs at the beginning of every remote session to prepare the environment.
# This repository is currently empty — extend this script as the project grows.

set -euo pipefail

# Only run in Claude Code remote (web) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> SessionStart hook: preparing environment..."

# ─────────────────────────────────────────────────────────────────────────────
# Add dependency installation commands here as the project grows.
# Examples (uncomment/adapt as needed):
#
# Node.js / npm:
#   npm install
#
# Node.js / yarn:
#   yarn install --frozen-lockfile
#
# Python / pip:
#   pip install -r requirements.txt
#
# Python / Poetry:
#   poetry install --no-interaction
#
# Python / uv:
#   uv sync
#
# Rust / Cargo:
#   cargo build
#
# Go:
#   go mod download
#
# Ruby / Bundler:
#   bundle install
# ─────────────────────────────────────────────────────────────────────────────

echo "==> SessionStart hook: done."
