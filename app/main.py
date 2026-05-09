import logging
from app.store import init_db, job_exists, save_job
from app.config_loader import load_companies
from app.dedupe import make_job_id
from app.notifier import send_discord
from app.scrapers.router import get_scraper
from app.discovery import DiscoveryService

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run(enable_discovery=False):
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
        logging.info(f"--- Checking: {name} ---")

        try:
            scraper = get_scraper(company_config)
            raw_data = scraper.fetch(url)
            jobs = scraper.parse(raw_data)
            
            new_jobs_count = 0
            for job in jobs:
                # Normalize job data
                job.company = name
                job.id = make_job_id(job.company, job.title, job.location, job.url)
                
                if job_exists(job.id):
                    logging.info(f"Reached existing job for {name}. Stopping further scans for this company.")
                    break
                
                save_job(job)
                try:
                    send_discord(job)
                    new_jobs_count += 1
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
    run(enable_discovery=discovery_mode)
