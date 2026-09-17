#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Activate the virtual environment and start uvicorn
exec .venv.bak/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
