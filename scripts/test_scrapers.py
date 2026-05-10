import os
import time
import logging
import requests
from app.store import init_db
from app.notifier import send_discord, send_telegram, WEBHOOK_URL, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, escape_markdown
from app.scrapers.router import get_scraper
from app.dedupe import make_job_id

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load test-specific environment variables
TEST_WEBHOOK_URL = os.getenv("TEST_DISCORD_WEBHOOK_URL")
TEST_CHAT_ID = os.getenv("TEST_TELEGRAM_CHAT_ID")

# If test variables exist, override the standard ones for this script
if TEST_WEBHOOK_URL:
    import app.notifier
    app.notifier.WEBHOOK_URL = TEST_WEBHOOK_URL
    WEBHOOK_URL = TEST_WEBHOOK_URL

if TEST_CHAT_ID:
    import app.notifier
    app.notifier.TELEGRAM_CHAT_ID = TEST_CHAT_ID
    TELEGRAM_CHAT_ID = TEST_CHAT_ID

# Override DB Path for testing
TEST_DB = "data/test_jobs.db"
if os.path.exists(TEST_DB):
    try:
        os.remove(TEST_DB)
    except:
        pass
os.environ["DB_PATH"] = TEST_DB

def send_test_marker(text):
    """Sends a simple text marker to both channels"""
    logging.info(f"Sending marker: {text}")
    
    # Discord
    if WEBHOOK_URL:
        try:
            requests.post(WEBHOOK_URL, json={"content": f"🛠️ **{text}**"})
        except Exception as e:
            logging.error(f"Failed to send Discord marker: {e}")
    
    # Telegram
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": f"🛠️ *{escape_markdown(text)}*",
                "parse_mode": "MarkdownV2"
            })
        except Exception as e:
            logging.error(f"Failed to send Telegram marker: {e}")

def run_test():
    init_db()
    
    test_cases = [
        {
            "name": "Pronto AI (Greenhouse)",
            "url": "https://boards.greenhouse.io/pronto",
            "type": "greenhouse"
        },
        {
            "name": "Flowlife (Lever)",
            "url": "https://jobs.lever.co/flowlife",
            "type": "lever"
        },
        {
            "name": "Parsons (Workday)",
            "url": "https://parsons.wd5.myworkdayjobs.com/en-US/Search",
            "type": "workday"
        },
        {
            "name": "AECOM (SmartRecruiters)",
            "url": "https://jobs.smartrecruiters.com/sr-jobs/search?limit=1&companyIdentifier=aecom",
            "type": "smartrecruiters"
        },
        {
            "name": "Workable Test",
            "url": "https://jobs.workable.com/api/v1/jobs?location=Saudi%20Arabia&limit=1",
            "type": "workable"
        }
    ]

    send_test_marker("TEST STARTED")

    for test in test_cases:
        logging.info(f"Testing scraper: {test['name']}")
        try:
            scraper = get_scraper(test)
            raw_data = scraper.fetch(test["url"])
            jobs = scraper.parse(raw_data)
            
            if jobs:
                job = jobs[0]
                # Normalize company name (fallback to test name if empty)
                if not job.company or job.company == "Unknown":
                    job.company = test["name"]

                job.id = make_job_id(job.company, job.title, job.location, job.url)
                
                logging.info(f"Successfully scraped job from {test['type']}: {job.title} at {job.company}")
                
                # Send notifications
                send_discord(job)
                send_telegram(job)
                
                # Rate limiting delay
                time.sleep(4)
            else:
                logging.warning(f"No jobs found for {test['name']}")
        
        except Exception as e:
            logging.error(f"Test failed for {test['name']}: {e}")

    send_test_marker("TEST ENDED")

if __name__ == "__main__":
    run_test()
