import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def format_posted_at(posted_at):
    if not posted_at:
        return "Unknown"

    try:
        try:
            ts = float(posted_at)

            if ts > 1e11:
                ts /= 1000

            dt = datetime.fromtimestamp(ts, tz=timezone.utc)

        except:
            clean_date = posted_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_date)

        diff = datetime.now(timezone.utc) - dt

        if diff.days == 0:
            hours = diff.seconds // 3600

            if hours == 0:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"

            return f"{hours} hours ago"

        if diff.days == 1:
            return "Yesterday"

        return f"{diff.days} days ago"

    except:
        return str(posted_at)


def send_discord(job):
    if not WEBHOOK_URL:
        raise ValueError("DISCORD_WEBHOOK_URL not set")

    payload = {
        "embeds": [
            {
                "color": 0x2B2D31,
                "author": {
                    "name": "New Opportunity Available"
                },
                "title": job.title,
                "url": job.url,
                "description": (
                    f"**Company:** {job.company}\n"
                    f"**Location:** {job.location}\n"
                    f"**Posted:** {format_posted_at(job.posted_at)}"
                ),
                "fields": [
                    {
                        "name": "🔗 Apply Here",
                        "value": f"[Click to Apply]({job.url})",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "Job Hunter Bot"
                    },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "content": "@everyone"
    }

    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code not in (200, 204):
        print("Failed to send Discord notification")
        print(response.text)
