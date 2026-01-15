import requests
import time
import random
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from .config import (
    BASE_URL, DEFAULT_START_PATH, MAX_WORKERS, MAX_DEPTH, MAX_CHILDREN,
    SLEEP_TIME, RETRY_ATTEMPTS
)
import py_crawler.db as db
from py_crawler.progress import CrawlStats

def print_log(message, log_file):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line + "\n")

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
        return url, [], 0, False

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Rough article word count: main content text only
    content_root = soup.find(id="mw-content-text")
    text = content_root.get_text(separator=" ", strip=True) if content_root else soup.get_text(" ", strip=True)
    word_count = len([w for w in text.split() if w.isalpha()])

    all_links = {
        (a['href'], a.get_text(strip=True))
        for a in soup.find_all('a', href=True)
        if is_valid_wiki_link(a['href'])
    }

    filtered = [
        href
        for href, text in all_links
        if matches_topic(href, text, topics)
    ]
    sampled = filtered if MAX_CHILDREN == -1 else random.sample(filtered, min(MAX_CHILDREN, len(filtered)))
    return url, sampled, word_count, True


def crawl_bfs_threaded(start_path, max_pages, log_file, topics, max_depth, enumeration=False, max_workers=MAX_WORKERS):
    stats = CrawlStats(topics, max_depth)
    queue = deque([(start_path, 0)])
    retry_queue = deque()
    db.insert_page(start_path, force=True)

    session_crawled = 0

    try:
        while queue and session_crawled < max_pages:
            batch = []
            while queue and len(batch) < MAX_WORKERS:
                url, depth = queue.popleft()
                if (max_depth < 0 or depth <= max_depth) and not db.is_crawled(url):
                    batch.append((url, depth))

            stats.update(queued=len(queue) + len(batch))

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(fetch_links, url, log_file, topics): (url, depth) for url, depth in batch
                }
                for future in as_completed(futures):
                    url, links, word_count, success = future.result()
                    original_url, depth = futures[future]

                    if success:
                        db.insert_links(url, links)
                        db.mark_crawled(url)
                        session_crawled += 1
                        stats.update(crawled=1, depth=depth)

                        print_log(f"✅ Crawled {url} → {len(links)} topic-matched links", log_file)

                        if enumeration:
                            print_log(f"[Depth {depth}] Parent: {url}", log_file)
                            for child in links:
                                print_log(f" └─ {child}", log_file)

                        for link in links:
                            queue.append((link, depth + 1))
                    else:
                        retry_queue.append((url, 0))
                        stats.update(failed=1)

            time.sleep(SLEEP_TIME)

        while retry_queue and session_crawled < max_pages:
            url, attempts = retry_queue.popleft()
            if attempts >= RETRY_ATTEMPTS:
                print_log(f"❌ Giving up on {url} after {RETRY_ATTEMPTS} attempts.", log_file)
                continue

            url, links, word_count, success = fetch_links(url, log_file, topics)
            if success:
                db.insert_links(url, links)
                db.mark_crawled(url)
                session_crawled += 1
                stats.update(crawled=1, depth=1)
                print_log(f"✅ RETRY Success {url} → {len(links)} links", log_file)

                if enumeration:
                    print_log(f"[Retry Depth 1] Parent: {url}", log_file)
                    for child in links:
                        print_log(f" └─ {child}", log_file)

                for link in links:
                    queue.append((link, 1))
            else:
                retry_queue.append((url, attempts + 1))
                stats.update(failed=1, retries=1)

            time.sleep(SLEEP_TIME)

    finally:
        stats.stop()
        print_log("✅ Crawl complete. Dashboard closed.", log_file)

def main_old():
    print("🚀 Wiki Crawler started!")
    parser = argparse.ArgumentParser(
        description="Multi-threaded Wikipedia BFS crawler with optional topic filter."
    )
    parser.add_argument(
        "--limit", type=int, default=500,
        help="Max pages to crawl per session"
    )
    parser.add_argument(
        "--depth", type=int, default=2,
        help="Maximum crawl depth from the starting page"
    )
    parser.add_argument(
        "--logfile", type=str, default="crawler.log",
        help="Path to log file"
    )
    parser.add_argument(
        "--topics", type=str,
        help="Comma-separated list of topic keywords to filter links"
    )
    parser.add_argument(
        "--enumerate", action="store_true",
        help="Log the child links grouped by their parent at each depth"
    )
    args = parser.parse_args()

    topic_list = [t.strip().lower() for t in args.topics.split(",")] if args.topics else []

    db.create_tables()
    start_path = db.get_next_uncrawled()
    if not start_path:
        print_log("No uncrawled pages in DB. Starting from default seed.", args.logfile)
        start_path = DEFAULT_START_PATH

    print_log(f"🔍 Filtering links by topics: {topic_list}" if topic_list else "🌐 No topic filtering applied", args.logfile)
    crawl_bfs_threaded(start_path, args.limit, args.logfile, topic_list, args.depth, args.enumerate)

if __name__ == "__main__":
    from py_crawler.cli import main
    main()
