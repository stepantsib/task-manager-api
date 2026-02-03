from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

app = FastAPI(title="Task Manager API")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"db": "ok"}
