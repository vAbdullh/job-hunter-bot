import os
import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_discord(job):
    if not WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL not set")

    payload = {
        "content": (
            f"🚀 New Job Found!\n"
            f"**{job.title}**\n"
            f"🏢 {job.company}\n"
            f"📍 {job.location}\n"
            f"🔗 {job.url}\n\n"
            f"@everyone @wpo"
        )
    }

    requests.post(WEBHOOK_URL, json=payload)
