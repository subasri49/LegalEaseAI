#!/usr/bin/env bash
# macOS / Linux / Git-Bash: starts backend + frontend together. Ctrl+C stops both.
uvicorn legalEaseAPI.main:app --reload --port 8000 &
BACK=$!
trap "kill $BACK" EXIT
streamlit run frontend/app.py
