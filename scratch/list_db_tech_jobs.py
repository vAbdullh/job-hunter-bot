import sqlite3
import os
import sys

# Ensure app package is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.notifier import is_technical_job

def list_tech_jobs():
    db_path = "data/jobs.db"
    if not os.path.exists(db_path):
        print("Database does not exist yet.")
        return
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT title, company, location FROM jobs")
    rows = cur.fetchall()
    conn.close()
    
    print(f"Total jobs in DB: {len(rows)}")
    print("=" * 60)
    print("JOBS DETECTED AS TECH:")
    print("=" * 60)
    
    tech_count = 0
    for title, company, location in rows:
        if is_technical_job(title):
            tech_count += 1
            print(f"- {title} | {company} ({location or 'N/A'})")
            
    print("=" * 60)
    print(f"Total Tech Jobs Detected: {tech_count}")

if __name__ == "__main__":
    list_tech_jobs()
