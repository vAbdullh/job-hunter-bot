import requests
import json
from urllib.parse import urljoin
from app.scrapers.base import BaseScraper
from app.models import Job

class WorkdayScraper(BaseScraper):
    def fetch(self, url: str):
        # Workday URLs: https://{tenant}.wd3.myworkdayjobs.com/en-US/{subdomain}
        parts = url.rstrip("/").split("/")
        domain = parts[2]
        tenant = domain.split(".")[0]
        subdomain = parts[-1]
        
        api_url = f"https://{domain}/wday/cxs/{tenant}/{subdomain}/jobs"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Origin": f"https://{domain}",
            "Referer": url,
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        payload = {
            "appliedFacets": {},
            "limit": 20,
            "offset": 0,
            "searchText": ""
        }
        
        try:
            # First attempt
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            if response.status_code == 422:
                # Try with a different subdomain derivation if it was en-US
                # Some sites have /en-US/External but API is /External
                if "en-US" in parts:
                    api_url = f"https://{domain}/wday/cxs/{tenant}/{subdomain}/jobs"
                    # Wait, it's already using parts[-1] which is External.
                    # Maybe it needs languageCode in payload
                    payload["languageCode"] = "en-US"
                    response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            
            response.raise_for_status()
            return {"data": response.json(), "base_url": f"https://{domain}/en-US/{subdomain}"}
        except Exception as e:
            raise e

    def parse(self, raw_data):
        jobs = []
        data = raw_data["data"]
        base_url = raw_data["base_url"]
        
        for item in data.get("jobPostings", []):
            # Construct full URL: base_url + externalPath
            external_path = item.get("externalPath")
            full_url = urljoin(base_url + "/", external_path.lstrip("/")) if external_path else base_url
            
            jobs.append(Job(
                id="",
                title=item.get("title"),
                company="",
                location=item.get("locationsText"),
                url=full_url,
                posted_at=item.get("postedOn")
            ))
        return jobs
