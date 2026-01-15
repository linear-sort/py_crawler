# config.py

# You can change this to an external path later
import os

DEFAULT_DB_PATH = "wiki_links.db"
ENV_DB_PATH_VAR = "WIKI_CRAWLER_DB"

def get_db_path():
    return os.getenv(ENV_DB_PATH_VAR, DEFAULT_DB_PATH)

# BFS crawl depth
# -1 or None gives no depth max
MAX_DEPTH = -1
MAX_WORKERS = 10

# Limit links explored per page
# -1 gives no limit
MAX_CHILDREN = -1

# Delay between requests
SLEEP_TIME = 0.1

# Start here if database is empty
DEFAULT_START_PATH = "/wiki/Web_crawler"

# Base Wikipedia URL
BASE_URL = "https://en.wikipedia.org"
MAX_SESSION_PAGES = 500
RETRY_ATTEMPTS = 2

LOG_FILE = "crawler.log"