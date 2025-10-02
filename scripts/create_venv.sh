#!/usr/bin/env zsh
set -euo pipefail

# Usage:
#   ./scripts/create_venv.sh            # use default python3
#   PYTHON=python3.11 ./scripts/create_venv.sh

PYTHON_EXEC="${PYTHON:-python3}"

echo "Using Python executable: $PYTHON_EXEC"

if ! command -v "$PYTHON_EXEC" >/dev/null 2>&1; then
  echo "Error: Python executable '$PYTHON_EXEC' not found on PATH." >&2
  exit 2
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
  echo "Creating .venv with $PYTHON_EXEC..."
  "$PYTHON_EXEC" -m venv .venv
else
  echo ".venv already exists — using existing virtual environment."
fi

# Activate
# shellcheck disable=SC1091
source .venv/bin/activate

echo "Upgrading pip, setuptools, wheel..."
python -m pip install --upgrade pip setuptools wheel

if [ -f requirements.txt ] && [ -s requirements.txt ]; then
  echo "Installing from requirements.txt..."
  if python -m pip install -r requirements.txt; then
    echo "Requirements installed successfully."
  else
    echo "pip failed to install requirements. See output above." >&2
    echo "Try setting PYTHON to a stable python (eg. PYTHON=python3.11) or install system build tools." >&2
    exit 3
  fi
else
  echo "No requirements to install (requirements.txt missing or empty)."
fi

echo "Done. Activate with: source .venv/bin/activate"
