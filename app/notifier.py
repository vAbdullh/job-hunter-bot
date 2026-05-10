import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def escape_markdown(text):
    """
    Escapes reserved characters for Telegram MarkdownV2.
    """
    if not text:
        return ""
    # Reserved characters in MarkdownV2
    reserved = r"_*[]()~`>#+-=|{}.!"
    for char in reserved:
        text = str(text).replace(char, f"\\{char}")
    return text


def format_posted_at(posted_at, lang="en"):
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
                if lang == "ar":
                    return f"{minutes} دقيقة"
                return f"{minutes} minutes ago"

            if lang == "ar":
                return f"{hours} ساعة"
            return f"{hours} hours ago"

        if diff.days == 1:
            if lang == "ar":
                return "امس"
            return "Yesterday"

        if lang == "ar":
            return f"{diff.days} يوماً"
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


def send_telegram(job):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Telegram credentials not set")
# make it arabic
    message = (
        f"🟢 *وظيفة جديدة* \\| _{escape_markdown(job.location or 'Saudi Arabia')}_\n\n"
        f"*المسمى الوظيفي:* {escape_markdown(job.title)}\n"
        f"*الشركة:* {escape_markdown(job.company)}\n"
        f"*الموقع:* {escape_markdown(job.location or 'N/A')}\n"
        f"*منذ:* {escape_markdown(format_posted_at(job.posted_at, 'ar'))}\n\n"
        f"[🔗 رابط التقديم]({job.url})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "MarkdownV2"
    }

    response = requests.post(url, json=payload)
    
    if response.status_code == 429:
        retry_after = response.json().get("parameters", {}).get("retry_after", 5)
        print(f"Telegram rate limit reached. Sleeping for {retry_after} seconds...")
        time.sleep(retry_after + 1)
        response = requests.post(url, json=payload) # Retry once

    if response.status_code != 200:
        print("Failed to send Telegram notification")
        print(response.text)
