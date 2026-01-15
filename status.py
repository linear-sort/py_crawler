# status.py
from py_crawler import db


def get_stats():
    with db.get_connection() as conn:
        cur = conn.cursor()

        total_pages = cur.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
        crawled_pages = cur.execute("SELECT COUNT(*) FROM pages WHERE crawled = 1").fetchone()[0]
        uncrawled_pages = total_pages - crawled_pages
        total_links = cur.execute("SELECT COUNT(*) FROM links").fetchone()[0]

        print("📊 Wikipedia Crawler Status")
        print("----------------------------")
        print(f"Total pages discovered : {total_pages}")
        print(f"Pages crawled          : {crawled_pages}")
        print(f"Pages remaining        : {uncrawled_pages}")
        print(f"Total link relationships: {total_links}")
        print("----------------------------")
        if uncrawled_pages == 0:
            print("✅ All discovered pages have been crawled.")
        else:
            print("🚧 Crawl in progress.")

if __name__ == "__main__":
    get_stats()
