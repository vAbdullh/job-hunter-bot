import requests
from app.scrapers.base import BaseScraper
from app.models import Job

class LeverScraper(BaseScraper):
    def fetch(self, url: str):
        # Convert jobs.lever.co/{company} to API URL
        company_token = url.split("/")[-1]
        api_url = f"https://api.lever.co/v0/postings/{company_token}"
        
        try:
            response = requests.get(api_url, timeout=10)
            response.raise_for_status()
            return {"type": "json", "data": response.json()}
        except Exception as e:
            # Fallback to HTML
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return {"type": "html", "data": response.text, "base_url": url}

    def parse(self, raw_data):
        jobs = []
        if raw_data["type"] == "json":
            for item in raw_data["data"]:
                jobs.append(Job(
                    id="",
                    title=item.get("text"),
                    company="",
                    location=item.get("categories", {}).get("location"),
                    url=item.get("hostedUrl")
                ))
        else:
            # HTML parsing for Lever
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            soup = BeautifulSoup(raw_data["data"], "html.parser")
            for item in soup.select(".posting"):
                link = item.select_one("a.posting-title")
                loc = item.select_one(".location")
                title_elem = item.select_one("h5")
                if link and title_elem:
                    title = title_elem.get_text(strip=True)
                    url = urljoin(raw_data["base_url"], link.get("href"))
                    location = loc.get_text(strip=True) if loc else "N/A"
                    jobs.append(Job(id="", title=title, company="", location=location, url=url))
        return jobs
