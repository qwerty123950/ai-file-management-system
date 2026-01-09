#!/bin/bash
source venv/bin/activate
docker start qdrant
uvicorn backend.main:app --reload &
streamlit run frontend/app.py
