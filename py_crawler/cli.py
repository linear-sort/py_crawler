import argparse
from py_crawler.config import DEFAULT_START_PATH
import py_crawler.db as db
from py_crawler.wiki_crawler import crawl_bfs_threaded, print_log
from py_crawler.export import export_to_json
from py_crawler.analyze import analyze_graph
from .config import MAX_WORKERS


def crawl_command(args):
    print("🚀 CLI started")

    topic_list = [t.strip().lower() for t in args.topics.split(",")] if args.topics else []

    db.create_tables()
    start_path = db.get_next_uncrawled(topic_list)

    if not start_path:
        print_log("No uncrawled pages in DB. Starting from default seed.", args.logfile)
        start_path = DEFAULT_START_PATH
        db.insert_page(start_path, force=True)

    print_log(
        f"🔍 Filtering links by topics: {topic_list}" if topic_list else "🌐 No topic filtering applied",
        args.logfile
    )

    crawl_bfs_threaded(
        start_path=start_path,
        max_pages=args.limit,
        log_file=args.logfile,
        topics=topic_list,
        max_depth=args.depth,
        enumeration=args.enumerate,
        max_workers=args.workers or MAX_WORKERS
    )


def export_command(args):
    export_to_json(output_path=args.output)


def analyze_command(args):
    analyze_graph()


def main():
    parser = argparse.ArgumentParser(description="Wikipedia Crawler CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── Crawl Command ─────────────────────────────────────────────
    crawl_parser = subparsers.add_parser("crawl", help="Start or resume crawl")
    crawl_parser.add_argument("--limit", type=int, default=100, help="Max pages to crawl")
    crawl_parser.add_argument("--logfile", type=str, default="crawler.log")
    crawl_parser.add_argument("--depth", type=int, default=-1)
    crawl_parser.add_argument("--topics", type=str, default="")
    crawl_parser.add_argument("--enumerate", action="store_true")
    crawl_parser.add_argument("--workers", type=int, help="Override max thread count")
    crawl_parser.set_defaults(func=crawl_command)

    # ── Export Command ────────────────────────────────────────────
    export_parser = subparsers.add_parser("export", help="Export crawled links to JSON")
    export_parser.add_argument("--output", type=str, default="links.json")
    export_parser.set_defaults(func=export_command)

    # ── Analyze Command ───────────────────────────────────────────
    analyze_parser = subparsers.add_parser("analyze", help="Print link graph stats")
    analyze_parser.set_defaults(func=analyze_command)

    # ── Parse and Execute ─────────────────────────────────────────
    args = parser.parse_args()
    args.func(args)
