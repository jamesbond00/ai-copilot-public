#!/usr/bin/env bash
# Helper for launching the AI Copilot FastAPI service under a process manager.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${VENV_PATH:-$ROOT_DIR/venv}"
REQUIREMENTS_FILE="${REQUIREMENTS_FILE:-$ROOT_DIR/requirements.txt}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
WORKERS="${WORKERS:-2}"

if [[ ! -d "$VENV_PATH" ]]; then
    echo "[run_api_service] Creating virtual environment at $VENV_PATH" >&2
    python3 -m venv "$VENV_PATH"
fi

source "$VENV_PATH/bin/activate"

if [[ ! -f "$VENV_PATH/.deps-installed" ]]; then
    echo "[run_api_service] Installing dependencies from $REQUIREMENTS_FILE" >&2
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    touch "$VENV_PATH/.deps-installed"
fi

cd "$ROOT_DIR"

args=(
    uvicorn
    src.api.main:app
    --host "$HOST"
    --port "$PORT"
    --workers "$WORKERS"
)

if [[ -n "${EXTRA_UVICORN_ARGS:-}" ]]; then
    # shellcheck disable=SC2206 # word splitting intentional to honor multiple flags
    extra_args=( ${EXTRA_UVICORN_ARGS} )
    args+=("${extra_args[@]}")
fi

exec "${args[@]}"
