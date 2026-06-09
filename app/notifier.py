import os
import re
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Technical jobs specific channels
WEBHOOK_URL_TECH = os.getenv("DISCORD_WEBHOOK_URL_TECH")
TELEGRAM_CHAT_ID_TECH = os.getenv("TELEGRAM_CHAT_ID_TECH")


def is_technical_job(title):
    if not title:
        return False
    title_lower = title.lower()
    
    # Direct tech keywords/roles
    direct_tech_keywords = [
        "developer", "programmer", "webmaster", "frontend", "front-end", 
        "backend", "back-end", "fullstack", "full-stack", "devops", "sysadmin", 
        "cybersecurity", "cyber security", "cloud", "ui/ux", "ux/ui", "helpdesk", "help desk",
        "data scientist", "data analyst", "data science", "data engineer",
        "database", "network administrator", "network specialist", "systems administrator",
        "information technology", "computer science", "software",
        "python", "javascript", "typescript", "react", "flutter", "laravel", "django", 
        "kubernetes", "docker", "aws", "azure", "gcp", "golang", "swift", "kotlin",
        # Arabic technical terms
        "مبرمج", "مطور", "برمجيات", "شبكات", "بيانات", "سحابية", 
        "أمن سيبراني", "أمن المعلومات", "دعم فني", "قواعد بيانات"
    ]
    
    for kw in direct_tech_keywords:
        if kw in title_lower:
            return True
            
    # Whole-word only keywords to avoid false positives (e.g. 'it' matching 'digital marketing specialist')
    whole_words = ["it", "ict", "dev", "tech", "web", "برمجة", "حاسب", "نظم"]
    for word in whole_words:
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, title_lower):
            return True
            
    # Engineer check (only count if it's a tech/IT/software engineer)
    if "engineer" in title_lower or "مهندس" in title_lower:
        tech_prefixes = [
            "software", "system", "network", "cloud", "devops", "data", "security", 
            "computer", "qa", "test", "web", "it", "infrastructure", "platform", "sre", 
            "fullstack", "full-stack", "frontend", "backend", "application", "support",
            # Arabic
            "برمجيات", "شبكات", "حاسب", "معلومات", "اتصالات", "نظم"
        ]
        for pref in tech_prefixes:
            if pref in title_lower:
                return True

    return False



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

    # Always send to the main/general channel
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code not in (200, 204):
        print("Failed to send Discord notification")
        print(response.text)

    # If it is a technical job and a technical webhook is configured, send to it as well
    if WEBHOOK_URL_TECH and is_technical_job(job.title):
        response_tech = requests.post(WEBHOOK_URL_TECH, json=payload)
        if response_tech.status_code not in (200, 204):
            print("Failed to send Discord notification to technical channel")
            print(response_tech.text)


def send_telegram(job):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Telegram credentials not set")

    message = (
        f"🟢 *وظيفة جديدة* \\| _{escape_markdown(job.location or 'Saudi Arabia')}_\n\n"
        f"*المسمى الوظيفي:* {escape_markdown(job.title)}\n"
        f"*الشركة:* {escape_markdown(job.company)}\n"
        f"*الموقع:* {escape_markdown(job.location or 'N/A')}\n"
        f"*منذ:* {escape_markdown(format_posted_at(job.posted_at, 'ar'))}\n\n"
        f"[🔗 رابط التقديم]({escape_markdown(job.url)})"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Send to the main/general Telegram channel
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "MarkdownV2"
    }
    _execute_telegram_send(url, payload)

    # If it is a technical job and a technical Telegram chat ID is configured, send to it as well
    if TELEGRAM_CHAT_ID_TECH and is_technical_job(job.title):
        payload_tech = {
            "chat_id": TELEGRAM_CHAT_ID_TECH,
            "text": message,
            "parse_mode": "MarkdownV2"
        }
        _execute_telegram_send(url, payload_tech)


def _execute_telegram_send(url, payload):
    response = requests.post(url, json=payload)
    
    if response.status_code == 429:
        retry_after = response.json().get("parameters", {}).get("retry_after", 5)
        print(f"Telegram rate limit reached. Sleeping for {retry_after} seconds...")
        time.sleep(retry_after + 1)
        response = requests.post(url, json=payload) # Retry once

    if response.status_code != 200:
        print(f"Failed to send Telegram notification to chat {payload.get('chat_id')}")
        print(response.text)

