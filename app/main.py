from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "match3"),
        user=os.getenv("DB_USER", "match3"),
        password=os.getenv("DB_PASSWORD")
    )

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id SERIAL PRIMARY KEY,
                player VARCHAR(50) NOT NULL,
                score INTEGER NOT NULL,
                level INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB init error: {e}")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return FileResponse("static/index.html")

class ScoreSubmit(BaseModel):
    player: str
    score: int
    level: int = 1

@app.post("/scores")
def save_score(data: ScoreSubmit):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO scores (player, score, level) VALUES (%s, %s, %s)",
            (data.player, data.score, data.level)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/scores")
def get_scores():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT player, score, level, created_at FROM scores ORDER BY score DESC LIMIT 10"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{"player": r[0], "score": r[1], "level": r[2], "date": str(r[3])} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))