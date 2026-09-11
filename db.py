"""
SQLite database layer for farmer accounts, profiles, and notifications.
"""

import sqlite3
import hashlib
import os
import secrets
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "khetgpt.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            land_size_acres REAL,
            crop TEXT,
            sowing_date TEXT,
            state TEXT,
            district TEXT,
            lat REAL,
            lon REAL,
            created_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_id INTEGER NOT NULL,
            type TEXT,
            message TEXT,
            created_at TEXT,
            is_read INTEGER DEFAULT 0,
            FOREIGN KEY (farmer_id) REFERENCES farmers(id)
        )
    """)
    conn.commit()
    conn.close()
    print(f"Database ready at {DB_PATH}")


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000).hex()
    return pwd_hash, salt


def create_farmer(username, password, land_size_acres=None, crop=None,
                   sowing_date=None, state=None, district=None, lat=None, lon=None):
    pwd_hash, salt = hash_password(password)
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO farmers
               (username, password_hash, salt, land_size_acres, crop, sowing_date, state, district, lat, lon, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, pwd_hash, salt, land_size_acres, crop, sowing_date, state, district, lat, lon,
             datetime.utcnow().isoformat())
        )
        conn.commit()
        return cur.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def verify_login(username, password):
    conn = get_conn()
    row = conn.execute("SELECT * FROM farmers WHERE username = ?", (username,)).fetchone()
    conn.close()
    if row is None:
        return None
    pwd_hash, _ = hash_password(password, row["salt"])
    if pwd_hash == row["password_hash"]:
        return dict(row)
    return None


def get_farmer(farmer_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM farmers WHERE id = ?", (farmer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_farmer(farmer_id, **fields):
    if not fields:
        return
    allowed = {"land_size_acres", "crop", "sowing_date", "state", "district", "lat", "lon"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    conn = get_conn()
    conn.execute(f"UPDATE farmers SET {set_clause} WHERE id = ?", (*updates.values(), farmer_id))
    conn.commit()
    conn.close()


def add_notification(farmer_id, ntype, message):
    conn = get_conn()
    conn.execute(
        "INSERT INTO notifications (farmer_id, type, message, created_at) VALUES (?, ?, ?, ?)",
        (farmer_id, ntype, message, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()


def get_notifications(farmer_id, limit=20):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM notifications WHERE farmer_id = ? ORDER BY created_at DESC LIMIT ?",
        (farmer_id, limit)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
    print("Tables created: farmers, notifications")
