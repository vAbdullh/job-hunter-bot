from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.workday import WorkdayScraper
from app.scrapers.generic import GenericHTMLScraper
from app.scrapers.smartrecruiters import SmartRecruitersScraper

def get_scraper(company_config):
    stype = company_config.get("type", "html").lower()
    
    if stype == "greenhouse":
        return GreenhouseScraper()
    elif stype == "lever":
        return LeverScraper()
    elif stype == "workday":
        return WorkdayScraper()
    elif stype in ["smartrecruiters", "api_json"]:
        return SmartRecruitersScraper()
    elif stype == "html":
        return GenericHTMLScraper(selector_config=company_config.get("selector"))
    else:
        # Default to generic HTML
        return GenericHTMLScraper()
