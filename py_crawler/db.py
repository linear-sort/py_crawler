import sqlite3
import os

DB_NAME = "wiki_links.db"

def get_db_path():
    return os.environ.get("WIKI_DB_PATH", DB_NAME)

def create_tables():
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pages (
                url TEXT PRIMARY KEY,
                crawled INTEGER DEFAULT 0,
                word_count INTEGER,
                out_links INTEGER
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS links (
                from_url TEXT,
                to_url TEXT,
                PRIMARY KEY (from_url, to_url)
            )
        """)
        conn.commit()

        if not _column_exists(conn, "pages", "word_count"):
            cursor.execute("ALTER TABLE pages ADD COLUMN word_count INTEGER")
        if not _column_exists(conn, "pages", "out_links"):
            cursor.execute("ALTER TABLE pages ADD COLUMN out_links INTEGER")
        conn.commit()

def _column_exists(conn, table, column):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(%s)" % table)
    return any(row[1] == column for row in cur.fetchall())

def set_page_metrics(url, word_count, out_links):
    with sqlite3.connect(get_db_path()) as conn:
        cur = conn.cursor()
        cur.execute(
            "UPDATE pages SET word_count=?, out_links=? WHERE url=?",
            (word_count, out_links, url)
        )
        conn.commit()


def insert_page(url, force=False):
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        if force:
            cursor.execute("INSERT OR REPLACE INTO pages (url, crawled) VALUES (?, 0)", (url,))
        else:
            cursor.execute("INSERT OR IGNORE INTO pages (url, crawled) VALUES (?, 0)", (url,))
        conn.commit()

def insert_links(from_url, to_urls):
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT OR IGNORE INTO pages (url, crawled) VALUES (?, 0)",
            [(url,) for url in to_urls]
        )
        cursor.executemany(
            "INSERT OR IGNORE INTO links (from_url, to_url) VALUES (?, ?)",
            [(from_url, to_url) for to_url in to_urls]
        )
        conn.commit()

def mark_crawled(url):
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE pages SET crawled = 1 WHERE url = ?", (url,))
        conn.commit()

def is_crawled(url):
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT crawled FROM pages WHERE url = ?", (url,))
        row = cursor.fetchone()
        return row and row[0] == 1

def get_next_uncrawled(topics=None):
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        if topics:
            conditions = " OR ".join("url LIKE ?" for _ in topics)
            params = [f"%{t.lower()}%" for t in topics]
            cursor.execute(
                f"SELECT url FROM pages WHERE crawled = 0 AND ({conditions}) LIMIT 1",
                params
            )
        else:
            cursor.execute("SELECT url FROM pages WHERE crawled = 0 LIMIT 1")

        row = cursor.fetchone()
        return row[0] if row else None

def get_all_links():
    with sqlite3.connect(get_db_path()) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT from_url, to_url FROM links")
        return cursor.fetchall()
