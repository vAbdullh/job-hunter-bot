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
            "searchText": "",
            "languageCode": "en-US"
        }
        
        try:
            # First attempt
            response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            if response.status_code == 422:
                # Try with a different subdomain derivation if it was en-US
                # Some sites have /en-US/External but API is /External
                if "en-US" in parts:
                    api_url = f"https://{domain}/wday/cxs/{tenant}/{subdomain}/jobs"
                    response = requests.post(api_url, headers=headers, json=payload, timeout=15)
            
            response.raise_for_status()
            return {"data": response.json(), "base_url": f"https://{domain}/en-US/{subdomain}"}
        except Exception as e:
            raise e

    def parse(self, raw_data):
        jobs = []
        data = raw_data["data"]
        base_url = raw_data["base_url"]
        domain = base_url.split("/")[2]
        tenant = domain.split(".")[0]
        subdomain = base_url.split("/")[-1]
        
        # Use a session for faster detail fetching
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        })

        for item in data.get("jobPostings", []):
            external_path = item.get("externalPath")
            full_url = urljoin(base_url + "/", external_path.lstrip("/")) if external_path else base_url
            
            bullets = item.get("bulletFields", [])
            location = item.get("locationsText")
            if not location and bullets:
                location = bullets[0]
            
            posted_at = item.get("postedOn")
            
            # If date is missing (common in some Workday sites), try a quick fetch of details
            if not posted_at and external_path:
                try:
                    # Construct detail API URL
                    detail_api = f"https://{domain}/wday/cxs/{tenant}/{subdomain}{external_path}"
                    resp = session.get(detail_api, timeout=5)
                    if resp.status_code == 200:
                        posted_at = resp.json().get("jobPostingInfo", {}).get("postedOn")
                except:
                    pass

            if not posted_at and bullets:
                for b in bullets:
                    if "Posted" in b or "Today" in b or "Yesterday" in b:
                        posted_at = b
                        break

            jobs.append(Job(
                id="",
                title=item.get("title"),
                company="Unknown",
                location=location,
                url=full_url,
                posted_at=posted_at
            ))
        return jobs
