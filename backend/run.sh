#!/usr/bin/env bash
# SIXCREP Backend — Arranca servidor API + sirve frontend
set -e
cd "$(dirname "$0")"

echo "📦 Instalando dependencias..."
pip install -q -r requirements.txt

echo "🚀 Iniciando servidor SIXCREP en http://localhost:8000"
echo "   Frontend: http://localhost:8000/static/panel_antofagasta.html"
echo "   API docs: http://localhost:8000/docs"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
