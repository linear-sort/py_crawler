# export.py

import sqlite3
import json
import csv
import argparse
from py_crawler.config import DEFAULT_DB_PATH
from py_crawler.db import get_all_links


def export_to_json_from_path(output_path):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT from_url, to_url FROM links")
    edges = [{"from": row[0], "to": row[1]} for row in cur.fetchall()]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2)
    print(f"✅ Exported {len(edges)} edges to {output_path}")

def export_to_json(filename="links.json"):
    links = get_all_links()

    graph = {}
    for from_url, to_url in links:
        graph.setdefault(from_url, []).append(to_url)

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)

    print(f"✅ Exported {len(links)} links to {filename}")

def export_to_csv(output_path):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT from_url, to_url FROM links")
    rows = cur.fetchall()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["from_url", "to_url"])
        writer.writerows(rows)
    print(f"✅ Exported {len(rows)} edges to {output_path}")

def export_crawled_pages(output_path):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT url FROM pages WHERE crawled = 1")
    urls = [row[0] for row in cur.fetchall()]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2)
    print(f"✅ Exported {len(urls)} crawled pages to {output_path}")

def export_subgraph(prefix, output_path):
    conn = sqlite3.connect(DEFAULT_DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT from_url, to_url FROM links WHERE from_url LIKE ?", (prefix + "%",))
    edges = [{"from": row[0], "to": row[1]} for row in cur.fetchall()]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(edges, f, indent=2)
    print(f"✅ Exported {len(edges)} edges from subgraph prefix '{prefix}' to {output_path}")

def parse_args():
    parser = argparse.ArgumentParser(description="Export Wikipedia link data from SQLite.")
    parser.add_argument("--json", metavar="FILE", help="Export full graph to JSON file")
    parser.add_argument("--csv", metavar="FILE", help="Export full graph to CSV file")
    parser.add_argument("--crawled", metavar="FILE", help="Export list of crawled pages to JSON file")
    parser.add_argument("--subgraph", metavar="PREFIX", help="Export subgraph starting from pages with this prefix")
    parser.add_argument("--output", metavar="FILE", default="subgraph.json", help="Output file for subgraph export")
    return parser.parse_args()

def cli():
    args = parse_args()

    if args.json:
        export_to_json(args.json)
    if args.csv:
        export_to_csv(args.csv)
    if args.crawled:
        export_crawled_pages(args.crawled)
    if args.subgraph:
        export_subgraph(args.subgraph, args.output)

    if not (args.json or args.csv or args.crawled or args.subgraph):
        print("❌ No export option selected. Use --help to see available options.")

def main():
    cli()
