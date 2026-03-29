"""
app/database.py
Async SQLite via aiosqlite + SQLAlchemy core (no ORM needed for this scale).
Stores projects so the frontend can re-load previous designs.
"""

import json
import uuid
from datetime import datetime, timezone
import os
from pathlib import Path

import aiosqlite

# For cloud deployments (Vercel, Render), use /tmp/ for writable storage if needed
if os.environ.get("VERCEL") or os.environ.get("RENDER"):
    DB_PATH = Path("/tmp/structai.db")
else:
    DB_PATH = Path("structai.db")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                params_json TEXT NOT NULL,
                result_json TEXT,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS interior_snapshots (
                id          TEXT PRIMARY KEY,
                project_id  TEXT NOT NULL,
                room        TEXT NOT NULL,
                style       TEXT NOT NULL,
                request_json TEXT NOT NULL,
                result_json  TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
        """)
        await db.commit()


# ── Project CRUD ──────────────────────────────────────────────────────────────

async def create_project(params_dict: dict, name: str | None = None, pid: str | None = None, result_dict: dict | None = None) -> str:
    pid = pid or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    label = name or f"Project {pid[:8].upper()}"
    res_json = json.dumps(result_dict) if result_dict else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO projects (id, name, params_json, result_json, created_at, updated_at) VALUES (?,?,?,?,?,?)",
            (pid, label, json.dumps(params_dict), res_json, now, now),
        )
        await db.commit()
    return pid


async def update_project(pid: str, params_dict: dict, result_dict: dict):
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE projects SET params_json=?, result_json=?, updated_at=? WHERE id=?",
            (json.dumps(params_dict), json.dumps(result_dict), now, pid),
        )
        await db.commit()


async def get_project(pid: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM projects WHERE id=?", (pid,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return dict(row)


async def list_projects(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def delete_project(pid: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM projects WHERE id=?", (pid,))
        await db.commit()
        return cur.rowcount > 0


# ── Interior snapshots ────────────────────────────────────────────────────────

async def save_interior(project_id: str, room: str, style: str,
                         req_dict: dict, result_dict: dict) -> str:
    sid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO interior_snapshots
               (id, project_id, room, style, request_json, result_json, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (sid, project_id, room, style, json.dumps(req_dict), json.dumps(result_dict), now),
        )
        await db.commit()
    return sid


async def get_interiors(project_id: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM interior_snapshots WHERE project_id=? ORDER BY created_at",
            (project_id,),
        ) as cur:
            return [dict(r) for r in await cur.fetchall()]
