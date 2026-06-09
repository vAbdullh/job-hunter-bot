import sqlite3
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def list_all_jobs():
    db_path = "data/jobs.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT title, company FROM jobs")
    rows = cur.fetchall()
    conn.close()
    
    for i, (title, company) in enumerate(rows, 1):
        print(f"{i}. {title} @ {company}")

if __name__ == "__main__":
    list_all_jobs()
