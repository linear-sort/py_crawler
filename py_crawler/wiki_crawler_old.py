import requests
import json
import os
import time
import random
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import networkx as nx
import matplotlib.pyplot as plt

BASE_URL = "https://en.wikipedia.org"
DEFAULT_START = "/wiki/Web_crawler"
MAX_DEPTH = 2
DATA_FILE = "../wiki_paths.json"
SLEEP_TIME = 0.1


def is_valid_wiki_link(href):
    return href.startswith("/wiki/") and ':' not in href and '#' not in href


def save_graph(graph):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2)


def load_graph():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}


def pick_next_start(graph):
    unexplored = set()
    for page, links in graph.items():
        for link in links:
            if link not in graph:
                unexplored.add(link)

    if unexplored:
        return random.choice(list(unexplored))
    return None


def crawl(path, graph, depth=0):
    if depth > MAX_DEPTH or path in graph:
        return

    url = urljoin(BASE_URL, path)
    print(f"Crawling [@{depth}]:", url)
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        if is_valid_wiki_link(href):
            links.add(href)

    graph[path] = sorted(links)
    save_graph(graph)
    print(f"Saving graph data with {len(links)} links for url: {path}")

    for href in links:
        crawl(href, graph, depth + 1)
        time.sleep(SLEEP_TIME)

def crawl_bfs(start_path, graph):
    queue = deque([(start_path, 0)])
    while queue:
        path, depth = queue.popleft()
        if depth > MAX_DEPTH or path in graph:
            continue

        url = urljoin(BASE_URL, path)
        print(f"Crawling [depth={depth}]: {url}")
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"  ⚠️ Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, 'html.parser')
        links = {
            a['href']
            for a in soup.find_all('a', href=True)
            if is_valid_wiki_link(a['href'])
        }

        graph[path] = sorted(links)
        save_graph(graph)
        print(f"  → Saved {len(links)} links for {path}")

        # Enqueue children
        # Limit to a random subset of 100 links if needed
        sampled_links = random.sample(list(links), min(100, len(links)))

        if len(links) > 100:
            print(f"  ⚠️  Truncated {len(links) - 100} links from {path}")

        for href in sampled_links:
            if href not in graph:
                queue.append((href, depth + 1))

        time.sleep(SLEEP_TIME)

def analyze_and_plot_graph(graph):
    print("\n--- Network Analysis ---")
    G = nx.DiGraph()

    for src, targets in graph.items():
        for dst in targets:
            G.add_edge(src, dst)

    print(f"Total nodes in graph: {G.number_of_nodes()}")
    print(f"Total edges in graph: {G.number_of_edges()}")

    top_out = sorted(G.out_degree, key=lambda x: x[1], reverse=True)[:10]
    print("Top 10 nodes by out-degree:")
    for node, degree in top_out:
        print(f"{node}: {degree} links")

    # Visualize a random subgraph of 100 nodes (if available)
    # sample_nodes = random.sample(list(G.nodes), min(100, len(G)))
    # subgraph = G.subgraph(sample_nodes)

    largest_cc = max(nx.weakly_connected_components(G), key=len)
    subgraph = G.subgraph(largest_cc).copy()

    sampled = list(subgraph.nodes)[:800]
    subgraph = subgraph.subgraph(sampled)

    print(f"Sample subgraph has {subgraph.number_of_nodes()} nodes and {subgraph.number_of_edges()} edges.")

    plt.figure(figsize=(14, 14))
    pos = nx.spring_layout(subgraph, k=0.25, seed=42)
    nx.draw_networkx_nodes(subgraph, pos, node_size=60)
    nx.draw_networkx_edges(subgraph, pos, edge_color='black', alpha=0.6, width=0.8, arrows=True, arrowsize=12)
    plt.title("Wikipedia Subgraph (Sample of 100 Nodes)")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    start_time = time.time()
    link_graph = load_graph()

    if not link_graph:
        print("No existing graph found. Starting from default:", DEFAULT_START)
        start_path = DEFAULT_START
    else:
        start_path = pick_next_start(link_graph)
        if start_path:
            print("Resuming from unexplored link:", start_path)
        else:
            print("All known links appear explored. No new links to crawl.")
            exit(0)

    # crawl(start_path, link_graph)
    crawl_bfs(start_path, link_graph)

    total_links = sum(len(links) for links in link_graph.values())
    avg_links = total_links / len(link_graph)
    all_links = set(link for links in link_graph.values() for link in links)
    unique_links = set(link for links in link_graph.values() for link in links)
    uncrawled = unique_links - set(link_graph.keys())

    crawled = set(link_graph.keys())
    missing = all_links - crawled

    print("Done!")
    print(f"Total links crawled: {total_links}")
    print(f"Average links per page: {avg_links:.2f}")
    print(f"Missing links: {len(missing)}")
    print("Total unique links captured:", len(unique_links))
    print("Uncrawled links:", len(uncrawled))

    analyze_and_plot_graph(link_graph)

    elapsed = time.time() - start_time
    mins, secs = divmod(elapsed, 60)
    print(f"\n⏱️ Elapsed time: {int(mins)}m {secs:.2f}s")

