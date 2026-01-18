#!/bin/bash
set -e

echo "▶ Activating virtual environment"
source venv/bin/activate

echo "▶ Checking Qdrant container"
if ! docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
  echo "▶ Starting Qdrant container"
  docker start qdrant
else
  echo "✔ Qdrant already running"
fi

echo "▶ Starting FastAPI backend"
uvicorn backend.main:app --reload &

echo "▶ Waiting for backend to be ready..."
sleep 5

echo "▶ Starting Streamlit frontend"
streamlit run frontend/app.py
