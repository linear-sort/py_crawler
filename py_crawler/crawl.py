# py_crawler/crawl.py

from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from .progress import CrawlStats
from .db import insert_page, insert_links, mark_crawled, is_crawled
from .utils import fetch_links, print_log

MAX_WORKERS = 8
RETRY_ATTEMPTS = 2


def crawl_bfs_threaded(start_path, max_pages, log_file, topics, max_depth, enumerate=False):
    stats = CrawlStats(topics, max_depth)
    queue = deque([(start_path, 0)])
    retry_queue = deque()
    insert_page(start_path)

    session_crawled = 0

    try:
        while queue and session_crawled < max_pages:
            batch = []
            while queue and len(batch) < MAX_WORKERS:
                url, depth = queue.popleft()
                if depth <= max_depth and not is_crawled(url):
                    batch.append((url, depth))

            stats.update(queued=len(queue) + len(batch))

            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {
                    executor.submit(fetch_links, url, log_file, topics): (url, depth) for url, depth in batch
                }
                for future in as_completed(futures):
                    url, links, success = future.result()
                    original_url, depth = futures[future]

                    if success:
                        insert_links(url, links)
                        mark_crawled(url)
                        session_crawled += 1
                        stats.update(crawled=1, depth=depth)

                        print_log(f"✅ Crawled {url} → {len(links)} topic-matched links", log_file)

                        if enumerate:
                            print_log(f"[Depth {depth}] Parent: {url}", log_file)
                            for child in links:
                                print_log(f" └─ {child}", log_file)

                        for link in links:
                            queue.append((link, depth + 1))
                    else:
                        retry_queue.append((url, 0))
                        stats.update(failed=1)

            time.sleep(0.1)

        while retry_queue and session_crawled < max_pages:
            url, attempts = retry_queue.popleft()
            if attempts >= RETRY_ATTEMPTS:
                print_log(f"❌ Giving up on {url} after {RETRY_ATTEMPTS} attempts.", log_file)
                continue

            url, links, success = fetch_links(url, log_file, topics)
            if success:
                insert_links(url, links)
                mark_crawled(url)
                session_crawled += 1
                stats.update(crawled=1, depth=1)
                print_log(f"✅ RETRY Success {url} → {len(links)} links", log_file)

                if enumerate:
                    print_log(f"[Retry Depth 1] Parent: {url}", log_file)
                    for child in links:
                        print_log(f" └─ {child}", log_file)

                for link in links:
                    queue.append((link, 1))
            else:
                retry_queue.append((url, attempts + 1))
                stats.update(failed=1, retries=1)

            time.sleep(0.1)

    finally:
        stats.stop()
        print_log("✅ Crawl complete. Dashboard closed.", log_file)
