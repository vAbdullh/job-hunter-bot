import logging
import os
import time
from app.store import init_db, job_exists, save_job
from app.config_loader import load_companies
from app.dedupe import make_job_id
from app.notifier import send_discord, send_telegram
from app.scrapers.router import get_scraper
from app.discovery import DiscoveryService

from app.utils import get_job_age_minutes

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAX_AGE_HOURS = int(os.getenv("MAX_AGE_HOURS", 7))

def run(enable_discovery=False, enable_discord=True, enable_telegram=False):
    init_db()
    companies = load_companies()
    
    if enable_discovery:
        logging.info("Starting discovery service...")
        discovery = DiscoveryService()
        # Cities: jeddah, makkah, riyadh
        # Countries: saudi, saudi arabia, ksa, kingdom of saudi arabia
        keywords = ["Jeddah", "Makkah", "Riyadh", "Saudi", "Saudi Arabia", "KSA", "Kingdom of Saudi Arabia"]
        discovered_companies = discovery.discover_ats_urls(keywords)
        logging.info(f"Discovered {len(discovered_companies)} new job boards")
        companies.extend(discovered_companies)
    
    # Add SmartRecruiters search API scans
    search_keywords = ["jeddah", "makkah", "riyadh", "saudi"]
    for kw in search_keywords:
        companies.append({
            "name": f"SmartRecruiters Search ({kw})",
            "url": f"https://jobs.smartrecruiters.com/sr-jobs/search?limit=100&keyword={kw}",
            "type": "smartrecruiters"
        })
    
    # Add Workable API scans
    workable_keywords = ["Jeddah", "Makkah", "Riyadh", "Saudi Arabia", "KSA"]
    for kw in workable_keywords:
        companies.append({
            "name": f"Workable Search ({kw})",
            "url": f"https://jobs.workable.com/api/v1/jobs?location={kw}&day_range=7",
            "type": "workable"
        })

    logging.info(f"Processing total of {len(companies)} companies")

    for company_config in companies:
        name = company_config["name"]
        url = company_config["url"]
        is_search = "Search" in name
        logging.info(f"--- Checking: {name} ---")

        try:
            scraper = get_scraper(company_config)
            raw_data = scraper.fetch(url)
            jobs = scraper.parse(raw_data)
            
            new_jobs_count = 0
            for job in jobs:
                # Normalize job data
                if not job.company or job.company == "Unknown":
                    if is_search:
                        job.company = "Unknown Company"
                    else:
                        job.company = name
                
                job.id = make_job_id(job.company, job.title, job.location, job.url)
                
                if job_exists(job.id):
                    if is_search:
                        # For search results, we don't stop entirely because they might not be sorted
                        continue
                    else:
                        logging.info(f"Reached existing job for {name}. Stopping further scans for this company.")
                        break
                
                # Filter by age (7 hours)
                age_mins = get_job_age_minutes(job.posted_at)
                if age_mins > MAX_AGE_HOURS * 60:
                    if not is_search:
                        # If a company-specific board is sorted, we can stop
                        logging.info(f"Reached job older than {MAX_AGE_HOURS} hours for {name}. Stopping.")
                        break
                    else:
                        # For search results, just skip this job and check others
                        continue
                
                save_job(job)
                try:
                    if enable_discord:
                        send_discord(job)
                    if enable_telegram:
                        send_telegram(job)
                    new_jobs_count += 1
                    # Rate limiting: wait 4 seconds between notifications
                    time.sleep(4)
                except Exception as e:
                    logging.error(f"Failed to send notification for {job.title}: {e}")
            
            if new_jobs_count > 0:
                logging.info(f"Found and notified {new_jobs_count} new jobs for {name}")
            else:
                logging.info(f"No new jobs found for {name}")

        except Exception as e:
            logging.error(f"Error processing {name}: {e}")
            continue

if __name__ == "__main__":
    import sys
    discovery_mode = "--discover" in sys.argv
    
    # If no flags passed, default to Discord if available
    # If specific flags passed, follow them
    dis_flag = "--dis" in sys.argv
    tel_flag = "--tel" in sys.argv
    
    # Logic: if no notification flags are provided, we'll try to use what's in env
    # But if the user explicitly used flags, we only use those.
    if not dis_flag and not tel_flag:
        # Check env to decide defaults
        use_dis = os.getenv("DISCORD_WEBHOOK_URL") is not None
        use_tel = os.getenv("TELEGRAM_BOT_TOKEN") is not None
    else:
        use_dis = dis_flag
        use_tel = tel_flag

    run(enable_discovery=discovery_mode, enable_discord=use_dis, enable_telegram=use_tel)
