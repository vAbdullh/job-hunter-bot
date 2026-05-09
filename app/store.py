import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "data/jobs.db")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        url TEXT,
        posted_at TEXT
    )
    """)
    
    # Migration: Add posted_at if it doesn't exist
    try:
        cur.execute("ALTER TABLE jobs ADD COLUMN posted_at TEXT")
    except sqlite3.OperationalError:
        pass # Already exists

    conn.commit()
    conn.close()


def save_job(job):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO jobs (id, title, company, location, url, posted_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (job.id, job.title, job.company, job.location, job.url, job.posted_at))

    conn.commit()
    conn.close()


def job_exists(job_id: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
    result = cur.fetchone()

    conn.close()
    return result is not None
