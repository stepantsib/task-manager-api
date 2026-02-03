# Task Manager API

FastAPI backend for managing tasks.

## Run locally (Windows)

```bash
py -m venv .venv
.\.venv\Scripts\activate
pip install fastapi uvicorn[standard]
uvicorn app.main:app --reload
