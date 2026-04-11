import sqlite3
import json
import os
from datetime import datetime, timedelta

DB_PATH = "ekikrit.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            phone       TEXT PRIMARY KEY,
            step        TEXT DEFAULT 'start',
            profile     TEXT DEFAULT '{}',
            history     TEXT DEFAULT '[]',
            lang_code   TEXT DEFAULT 'hi',
            voice_mode  INTEGER DEFAULT 0,
            created_at  TEXT,
            updated_at  TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS matched_schemes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            phone           TEXT,
            scheme_name     TEXT,
            matched_at      TEXT,
            status          TEXT DEFAULT 'suggested',
            followup_date   TEXT,
            reminder_sent   INTEGER DEFAULT 0
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS scheduled_messages (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            phone       TEXT,
            message     TEXT,
            send_at     TEXT,
            sent        INTEGER DEFAULT 0,
            type        TEXT
        )
    """)

    conn.commit()
    conn.close()

def get_user(phone: str) -> dict:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE phone=?", (phone,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "step":       row["step"],
        "profile":    json.loads(row["profile"]),
        "history":    json.loads(row["history"]),
        "lang_code":  row["lang_code"],
        "voice_mode": bool(row["voice_mode"]),
    }

def save_user(phone: str, state: dict):
    conn = get_conn()
    now = datetime.now().isoformat()
    conn.execute("""
        INSERT INTO users (phone, step, profile, history, lang_code, voice_mode, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(phone) DO UPDATE SET
            step=excluded.step,
            profile=excluded.profile,
            history=excluded.history,
            lang_code=excluded.lang_code,
            voice_mode=excluded.voice_mode,
            updated_at=excluded.updated_at
    """, (
        phone,
        state.get("step", "start"),
        json.dumps(state.get("profile", {})),
        json.dumps(state.get("history", [])[-20:]),  # keep last 20 messages only
        state.get("lang_code", "hi"),
        int(state.get("voice_mode", False)),
        now, now
    ))
    conn.commit()
    conn.close()

def save_matched_schemes(phone: str, schemes: list):
    conn = get_conn()
    now = datetime.now()
    followup = (now + timedelta(days=12)).date().isoformat()

    for s in schemes:
        conn.execute("""
            INSERT INTO matched_schemes (phone, scheme_name, matched_at, status, followup_date)
            VALUES (?, ?, ?, 'suggested', ?)
        """, (phone, s["name"], now.isoformat(), followup))

    conn.commit()
    conn.close()

def schedule_message(phone: str, message: str, send_at: datetime, msg_type: str):
    conn = get_conn()
    conn.execute("""
        INSERT INTO scheduled_messages (phone, message, send_at, type)
        VALUES (?, ?, ?, ?)
    """, (phone, message, send_at.isoformat(), msg_type))
    conn.commit()
    conn.close()

def get_due_messages() -> list:
    conn = get_conn()
    now = datetime.now().isoformat()
    rows = conn.execute("""
        SELECT * FROM scheduled_messages
        WHERE sent=0 AND send_at <= ?
    """, (now,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_message_sent(msg_id: int):
    conn = get_conn()
    conn.execute("UPDATE scheduled_messages SET sent=1 WHERE id=?", (msg_id,))
    conn.commit()
    conn.close()

def get_followup_due() -> list:
    conn = get_conn()
    today = datetime.now().date().isoformat()
    rows = conn.execute("""
        SELECT DISTINCT phone, scheme_name FROM matched_schemes
        WHERE followup_date <= ? AND status='suggested' AND reminder_sent=0
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_followup_sent(phone: str):
    conn = get_conn()
    conn.execute("""
        UPDATE matched_schemes SET reminder_sent=1
        WHERE phone=? AND status='suggested'
    """, (phone,))
    conn.commit()
    conn.close()

def update_scheme_status(phone: str, scheme_name: str, status: str):
    conn = get_conn()
    conn.execute("""
        UPDATE matched_schemes SET status=?
        WHERE phone=? AND scheme_name=?
    """, (status, phone, scheme_name))
    conn.commit()
    conn.close()

init_db()