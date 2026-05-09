import requests
from bs4 import BeautifulSoup
import time
import logging
import urllib.parse
# from app.notifier import send_message  # Removed as requested

class DiscoveryService:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.session.headers.update(self.headers)

    def search_google(self, query):
        """
        Search Google for URLs. 
        Note: Google may block this if run too frequently.
        """
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.google.com/search?q={encoded_query}"
        
        logging.info(f"Searching Google for: {query}")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            urls = []
            # Standard Google Result
            for a in soup.select("a"):
                href = a.get("href")
                if href:
                    if "/url?q=" in href:
                        clean_url = href.split("/url?q=")[1].split("&")[0]
                        if "http" in clean_url and "google.com" not in clean_url:
                            urls.append(urllib.parse.unquote(clean_url))
                    elif href.startswith("http") and "google.com" not in href:
                        urls.append(href)
            
            # Mobile/Simplified result
            for div in soup.select(".kCrYT"):
                a = div.select_one("a")
                if a:
                    href = a.get("href")
                    if href and "/url?q=" in href:
                        clean_url = href.split("/url?q=")[1].split("&")[0]
                        urls.append(urllib.parse.unquote(clean_url))

            return list(set(urls))
        except Exception as e:
            logging.error(f"Google search failed: {e}")
            return []

    def search_duckduckgo(self, query):
        """
        Search DuckDuckGo for URLs. 
        """
        encoded_query = urllib.parse.quote(query)
        # Using the lite version which is easier to scrape
        url = f"https://duckduckgo.com/lite/?q={encoded_query}"
        
        logging.info(f"Searching DuckDuckGo Lite for: {query}")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            urls = []
            for a in soup.select("a.result-link"):
                href = a.get("href")
                if href:
                    urls.append(href)
            return urls
        except Exception as e:
            logging.error(f"DuckDuckGo search failed: {e}")
            return []

    def search_bing(self, query):
        """
        Search Bing for URLs.
        """
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.bing.com/search?q={encoded_query}"
        
        logging.info(f"Searching Bing for: {query}")
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            
            urls = []
            for h2 in soup.select("li.b_algo h2"):
                a = h2.select_one("a")
                if a:
                    urls.append(a.get("href"))
            return urls
        except Exception as e:
            logging.error(f"Bing search failed: {e}")
            return []

    def discover_ats_urls(self, keywords, sites=["myworkdayjobs.com", "lever.co", "greenhouse.io", "smartrecruiters.com"]):
        discovered = []
        for site in sites:
            # Also try with the dot as suggested by user
            site_variants = [site, f".{site}"]
            for site_var in site_variants:
                for kw in keywords:
                    query = f"site:{site_var} \"{kw}\""
                    
                    # Try Bing (often easier than Google/DDG now)
                    urls = self.search_bing(query)
                    
                    if not urls:
                        urls = self.search_duckduckgo(query)
                    
                    if not urls:
                        urls = self.search_google(query)
                    
                    for url in urls:
                        item = self._clean_ats_url(url, site)
                        if item:
                            logging.info(f"Found board: {item['name']} at {item['url']}")
                            discovered.append(item)
                    
                    time.sleep(1)
        
        # Deduplicate by URL
        unique_discovered = {item["url"]: item for item in discovered}.values()
        return list(unique_discovered)

    def _clean_ats_url(self, url, site):
        try:
            if site == "myworkdayjobs.com":
                # Match: https://{tenant}.wd3.myworkdayjobs.com/en-US/{subdomain}/...
                parts = url.split("/")
                # Search for en-US or similar locale
                for i, part in enumerate(parts):
                    if "-" in part and len(part) == 5: # e.g. en-US, ar-SA
                        if i + 1 < len(parts):
                            base = "/".join(parts[:i+2])
                            return {"name": f"Discovered Workday ({parts[2].split('.')[0]})", "url": base, "type": "workday"}
                    if part.lower() in ["external", "careers", "internal"]:
                        base = "/".join(parts[:i+1])
                        return {"name": f"Discovered Workday ({parts[2].split('.')[0]})", "url": base, "type": "workday"}
                
                if len(parts) >= 5:
                    base = "/".join(parts[:5])
                    return {"name": f"Discovered Workday", "url": base, "type": "workday"}

            elif site == "lever.co" and "jobs.lever.co" in url:
                parts = url.rstrip("/").split("/")
                if len(parts) >= 4:
                    base = "/".join(parts[:4])
                    return {"name": f"Discovered Lever ({parts[3]})", "url": base, "type": "lever"}

            elif site == "greenhouse.io" and "boards.greenhouse.io" in url:
                parts = url.rstrip("/").split("/")
                if len(parts) >= 4:
                    base = "/".join(parts[:4])
                    return {"name": f"Discovered Greenhouse ({parts[3]})", "url": base, "type": "greenhouse"}
            
            elif site == "smartrecruiters.com" and "jobs.smartrecruiters.com" in url:
                parts = url.rstrip("/").split("/")
                if len(parts) >= 4:
                    base = "/".join(parts[:4])
                    return {"name": f"Discovered SmartRecruiters ({parts[3]})", "url": base, "type": "html"}
        except:
            pass
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    service = DiscoveryService()
    results = service.discover_ats_urls(["Saudi Arabia", "Riyadh"])
    for r in results:
        # send_message(f"🔍 Discovered new board: {r['name']}\n🔗 {r['url']}")
        logging.info(f"Discovered new board: {r['name']} at {r['url']}")
