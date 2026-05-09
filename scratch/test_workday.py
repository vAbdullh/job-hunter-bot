import requests
import json

def test_workday(domain, tenant, subdomain):
    api_url = f"https://{domain}/wday/cxs/{tenant}/{subdomain}/jobs"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # Try different payloads
    payloads = [
        {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""},
        {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "", "languageCode": "en-US"},
        {}
    ]
    
    for i, p in enumerate(payloads):
        print(f"Testing payload {i}...")
        r = requests.post(api_url, headers=headers, json=p)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            print("Success!")
            # print(r.json().get("total", 0))
            return
        else:
            print(f"Response: {r.text[:200]}")

if __name__ == "__main__":
    test_workday("aramco.wd3.myworkdayjobs.com", "aramco", "External")
