import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.scrapers.base import BaseScraper
from app.models import Job

class GenericHTMLScraper(BaseScraper):
    def __init__(self, selector_config=None):
        self.selectors = selector_config or {
            "job_card": ".job-card",
            "title": ".title",
            "link": "a",
            "location": ".location"
        }

    def fetch(self, url: str):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # SmartRecruiters detection
        if "smartrecruiters.com" in url:
            company = url.rstrip("/").split("/")[-1]
            api_url = f"https://api.smartrecruiters.com/v1/companies/{company}/postings"
            try:
                r = requests.get(api_url, headers=headers, timeout=10)
                if r.status_code == 200:
                    return {"type": "smartrecruiters", "data": r.json()}
            except:
                pass

        try:
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
        except requests.exceptions.SSLError:
            # Fallback for sites with misconfigured SSL (like Red Sea Global)
            response = requests.get(url, headers=headers, timeout=15, verify=False)
            response.raise_for_status()
            
        return {"type": "html", "html": response.text, "base_url": response.url}

    def parse(self, raw_data):
        if raw_data.get("type") == "smartrecruiters":
            jobs = []
            for item in raw_data["data"].get("content", []):
                jobs.append(Job(
                    id="",
                    title=item.get("name"),
                    company="",
                    location=item.get("location", {}).get("city"),
                    url=f"https://jobs.smartrecruiters.com/{raw_data['data']['companySlug']}/{item['id']}"
                ))
            return jobs

        html = raw_data["html"]
        base_url = raw_data["base_url"]
        soup = BeautifulSoup(html, "html.parser")
        
        jobs = []
        cards = soup.select(self.selectors["job_card"])
        
        for card in cards:
            title_elem = card.select_one(self.selectors["title"])
            link_elem = card.select_one(self.selectors["link"])
            loc_elem = card.select_one(self.selectors["location"])
            
            if title_elem and link_elem:
                title = title_elem.get_text(strip=True)
                url = link_elem.get("href")
                if url:
                    url = urljoin(base_url, url)
                
                location = loc_elem.get_text(strip=True) if loc_elem else "N/A"
                
                jobs.append(Job(
                    id="",
                    title=title,
                    company="",
                    location=location,
                    url=url
                ))
        
        return jobs
