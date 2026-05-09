import requests
from app.scrapers.base import BaseScraper
from app.models import Job

class SmartRecruitersScraper(BaseScraper):
    def fetch(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.json()

    def parse(self, raw_data):
        jobs = []
        # Handle the search API format: https://jobs.smartrecruiters.com/sr-jobs/search
        for item in raw_data.get("content", []):
            jobs.append(Job(
                id="",
                title=item.get("name"),
                company=item.get("company", {}).get("name") or "Unknown",
                location=item.get("location", {}).get("city"),
                url=f"https://jobs.smartrecruiters.com/{item.get('company', {}).get('identifier')}/{item.get('id')}"
            ))
        return jobs
