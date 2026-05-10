import logging
from datetime import datetime, timezone, timedelta

def get_job_age_minutes(posted_at):
    """Calculates age in minutes from the posted_at string/timestamp"""
    if not posted_at:
        return 999999 # Unknown is assumed old
    
    try:
        try:
            # Try timestamp
            ts = float(posted_at)
            if ts > 1e11: ts /= 1000
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        except:
            # Try ISO format
            clean_date = str(posted_at).replace("Z", "+00:00")
            dt = datetime.fromisoformat(clean_date)
            # Ensure timezone aware
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)

        diff = datetime.now(timezone.utc) - dt
        return diff.total_seconds() / 60
    except:
        # For strings like "Posted Today", we can't know for sure
        # But we treat common relative strings
        text = str(posted_at).lower()
        if "minute" in text:
            try:
                return int(text.split()[0])
            except:
                return 1
        if "just now" in text:
            return 1
        if "hour" in text:
            try:
                return int(text.split()[0]) * 60
            except:
                return 60
        if "today" in text:
            return 60 * 12 # Assume middle of day
        return 999999 # Default to old for safety
