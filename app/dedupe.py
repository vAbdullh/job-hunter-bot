import hashlib


def make_job_id(company: str, title: str, location: str | None, url: str):
    raw = f"{company}|{title}|{location}|{url}"
    return hashlib.sha256(raw.encode()).hexdigest()
