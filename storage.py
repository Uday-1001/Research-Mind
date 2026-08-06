import sqlite3
import json
from datetime import datetime
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "sessions.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                topic TEXT,
                timestamp DATETIME,
                results_json TEXT
            )
        """)
        conn.commit()

def save_session(session_id: str, topic: str, results: dict):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO sessions (id, topic, timestamp, results_json)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                topic=excluded.topic,
                timestamp=excluded.timestamp,
                results_json=excluded.results_json
        """, (
            session_id, 
            topic, 
            datetime.now().isoformat(), 
            json.dumps(results)
        ))
        conn.commit()

def get_all_sessions():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        
        sessions = []
        for row in rows:
            sessions.append({
                "id": row["id"],
                "topic": row["topic"],
                "timestamp": row["timestamp"],
                "results": json.loads(row["results_json"])
            })
        return sessions

def delete_session(session_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
