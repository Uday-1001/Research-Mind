import sqlite3
import json
from datetime import datetime
import os

# Support persistent cloud disk path via DATABASE_PATH env var
DB_PATH = os.getenv("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "sessions.db"))

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL DEFAULT 'default',
                topic TEXT,
                timestamp DATETIME,
                results_json TEXT
            )
        """)
        # Dedicated table for registered and created workspaces
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workspaces (
                id TEXT PRIMARY KEY,
                created_at DATETIME
            )
        """)
        # Ensure default workspace is always registered
        conn.execute("INSERT OR IGNORE INTO workspaces (id, created_at) VALUES ('default', ?)", (datetime.now().isoformat(),))
        # Automatic schema migration: ensure workspace_id column exists
        cursor = conn.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        if "workspace_id" not in columns:
            conn.execute("ALTER TABLE sessions ADD COLUMN workspace_id TEXT NOT NULL DEFAULT 'default'")
        # High-performance index for tenant-scoped session lookups
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_workspace ON sessions (workspace_id, timestamp DESC)")
        conn.commit()

def save_session(session_id: str, topic: str, results: dict, workspace_id: str = "default"):
    clean_ws = (workspace_id or "default").strip()
    if not clean_ws:
        clean_ws = "default"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO sessions (id, workspace_id, topic, timestamp, results_json)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                workspace_id=excluded.workspace_id,
                topic=excluded.topic,
                timestamp=excluded.timestamp,
                results_json=excluded.results_json
        """, (
            session_id, 
            clean_ws,
            topic, 
            datetime.now().isoformat(), 
            json.dumps(results)
        ))
        # Ensure active workspace is recorded in workspaces registry
        conn.execute("INSERT OR IGNORE INTO workspaces (id, created_at) VALUES (?, ?)", (clean_ws, datetime.now().isoformat()))
        conn.commit()

def get_all_sessions(workspace_id: str = "default"):
    clean_ws = (workspace_id or "default").strip()
    if not clean_ws:
        clean_ws = "default"
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE workspace_id = ? ORDER BY timestamp DESC",
            (clean_ws,)
        )
        rows = cursor.fetchall()
        
        sessions = []
        for row in rows:
            sessions.append({
                "id": row["id"],
                "workspace_id": row["workspace_id"] if "workspace_id" in row.keys() else clean_ws,
                "topic": row["topic"],
                "timestamp": row["timestamp"],
                "results": json.loads(row["results_json"])
            })
        return sessions

def delete_session(session_id: str, workspace_id: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        if workspace_id:
            conn.execute("DELETE FROM sessions WHERE id = ? AND workspace_id = ?", (session_id, workspace_id.strip()))
        else:
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()

def get_session(session_id: str, workspace_id: str = None):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        if workspace_id:
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ? AND workspace_id = ?", (session_id, workspace_id.strip()))
        else:
            cursor = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "workspace_id": row["workspace_id"] if "workspace_id" in row.keys() else "default",
                "topic": row["topic"],
                "timestamp": row["timestamp"],
                "results": json.loads(row["results_json"])
            }
        return None

def workspace_exists(workspace_id: str) -> bool:
    clean_ws = (workspace_id or "").strip().lower()
    if not clean_ws:
        return False
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT 1 FROM workspaces WHERE id = ?
            UNION
            SELECT 1 FROM sessions WHERE workspace_id = ?
        """, (clean_ws, clean_ws))
        return cursor.fetchone() is not None

def create_workspace(workspace_id: str) -> str:
    clean_ws = (workspace_id or "").strip().replace(" ", "-").lower()
    if not clean_ws:
        clean_ws = "default"
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO workspaces (id, created_at) VALUES (?, ?)",
            (clean_ws, datetime.now().isoformat())
        )
        conn.commit()
    return clean_ws

def delete_workspace(workspace_id: str):
    clean_ws = (workspace_id or "").strip().lower()
    if not clean_ws or clean_ws == "default":
        return
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM workspaces WHERE id = ?", (clean_ws,))
        conn.execute("DELETE FROM sessions WHERE workspace_id = ?", (clean_ws,))
        conn.commit()

def get_all_workspaces():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT id FROM workspaces
            UNION
            SELECT DISTINCT workspace_id FROM sessions
            ORDER BY 1 ASC
        """)
        rows = cursor.fetchall()
        workspaces = [r[0] for r in rows if r[0]]
        if "default" not in workspaces:
            workspaces.insert(0, "default")
        return workspaces
