# py_crawler/utils.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime

from .config import (
    BASE_URL, DEFAULT_START_PATH, MAX_WORKERS, MAX_DEPTH, MAX_CHILDREN,
    SLEEP_TIME, RETRY_ATTEMPTS
)

def is_valid_wiki_link(href):
    return href.startswith("/wiki/") and ':' not in href and '#' not in href

def matches_topic(href, text, topics):
    if not topics:
        return True
    href_lower = href.lower()
    text_lower = text.lower()
    return any(topic in href_lower or topic in text_lower for topic in topics)

def fetch_links(url, log_file, topics):
    full_url = urljoin(BASE_URL, url)
    print_log(f"→ Fetching: {full_url}", log_file)
    try:
        resp = requests.get(full_url, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print_log(f"  ⚠️ Failed to fetch {full_url}: {e}", log_file)
        return url, [], False

    soup = BeautifulSoup(resp.text, 'html.parser')
    all_links = {
        (a['href'], a.get_text(strip=True))
        for a in soup.find_all('a', href=True)
        if is_valid_wiki_link(a['href'])
    }

    filtered = [
        href
        for href,text in all_links
        if matches_topic(href, text, topics)
    ]
    if MAX_CHILDREN == -1:
        sampled = filtered
    else:
        sampled = random.sample(filtered, min(MAX_CHILDREN, len(filtered)))
    return url, sampled, True

def print_log(msg, log_file=None):
    timestamp = datetime.utcnow().strftime("[%Y-%m-%d %H:%M:%S]")
    full_msg = f"{timestamp} {msg}"
    print(full_msg)
    if log_file:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(full_msg + "\n")
