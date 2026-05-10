import requests
from app.scrapers.base import BaseScraper
from app.models import Job

class WorkableScraper(BaseScraper):
    def fetch(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def parse(self, raw_data):
        jobs = []
        for item in raw_data.get("jobs", []):
            # Location handling (Workable can have multiple)
            location = item.get("location", {}).get("city") or "Saudi Arabia"
            
            jobs.append(Job(
                id="", # Will be set by make_job_id
                title=item.get("title"),
                company=(
                    item.get("company", {}).get("name") or 
                    item.get("company_name") or 
                    "Unknown"
                ),
                location=location,
                url=item.get("url"),
                posted_at=item.get("created")
            ))
        return jobs
