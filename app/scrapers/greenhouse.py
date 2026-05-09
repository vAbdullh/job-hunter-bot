import requests
from app.scrapers.base import BaseScraper
from app.models import Job

class GreenhouseScraper(BaseScraper):
    def fetch(self, url: str):
        # Handle both boards.greenhouse.io and job-boards.greenhouse.io
        company_token = url.rstrip("/").split("/")[-1]
        
        # Try both API endpoints
        api_urls = [
            f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs",
            f"https://api.greenhouse.io/v1/boards/{company_token}/jobs"
        ]
        
        for api_url in api_urls:
            try:
                response = requests.get(api_url, timeout=10)
                if response.status_code == 200:
                    return {"type": "json", "data": response.json()}
            except:
                continue
        
        # Fallback to HTML
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        response.raise_for_status()
        return {"type": "html", "data": response.text, "base_url": response.url}

    def parse(self, raw_data):
        jobs = []
        if raw_data["type"] == "json":
            for item in raw_data["data"].get("jobs", []):
                jobs.append(Job(
                    id="",
                    title=item.get("title"),
                    company="",
                    location=item.get("location", {}).get("name"),
                    url=item.get("absolute_url")
                ))
        else:
            # HTML parsing for Greenhouse
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            soup = BeautifulSoup(raw_data["data"], "html.parser")
            for item in soup.select(".opening"):
                link = item.select_one("a")
                loc = item.select_one(".location")
                if link:
                    title = link.get_text(strip=True)
                    url = urljoin(raw_data["base_url"], link.get("href"))
                    location = loc.get_text(strip=True) if loc else "N/A"
                    jobs.append(Job(id="", title=title, company="", location=location, url=url))
        return jobs
