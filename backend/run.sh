#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

if ! python -c "import fastapi" 2>/dev/null; then
    pip install fastapi uvicorn httpx reportlab
fi

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
