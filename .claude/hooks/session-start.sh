#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

VENV_DIR="$CLAUDE_PROJECT_DIR/.venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

# Install project with dev dependencies into venv
"$VENV_DIR/bin/pip" install -e "$CLAUDE_PROJECT_DIR/.[dev]"

# Persist venv activation for the session
echo "export PATH=\"$VENV_DIR/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
echo "export VIRTUAL_ENV=\"$VENV_DIR\"" >> "$CLAUDE_ENV_FILE"
