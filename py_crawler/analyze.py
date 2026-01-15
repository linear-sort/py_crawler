import py_crawler.db as db
from collections import defaultdict

def analyze_graph():
    links = db.get_all_links()
    print("📊 Link Graph Stats")

    out_degree = defaultdict(int)
    in_degree = defaultdict(int)

    for from_url, to_url in links:
        out_degree[from_url] += 1
        in_degree[to_url] += 1

    total_nodes = len(out_degree | in_degree)
    total_edges = len(links)
    avg_out = sum(out_degree.values()) / len(out_degree) if out_degree else 0
    avg_in = sum(in_degree.values()) / len(in_degree) if in_degree else 0

    print(f"• Nodes crawled: {total_nodes}")
    print(f"• Links (edges): {total_edges}")
    print(f"• Average out-degree: {avg_out:.2f}")
    print(f"• Average in-degree: {avg_in:.2f}")

    # Optional: Top 5 hubs
    top_out = sorted(out_degree.items(), key=lambda x: x[1], reverse=True)[:5]
    print("\n🏆 Top 5 pages by outbound links:")
    for url, count in top_out:
        print(f"  - {url} → {count} links")

        # --- Compute Rabbit-Hole Score (RHS) ---
        # Fetch per-page word_count and attach to dict
        import sqlite3
        from py_crawler.db import get_db_path
        conn = sqlite3.connect(get_db_path())
        cur = conn.cursor()
        cur.execute("SELECT url, COALESCE(word_count,0), COALESCE(out_links,0) FROM pages")
        page_words = {u: int(w) for (u, w, _) in cur.fetchall()}
        page_outlinks = {u: int(o) for (u, _, o) in
                         cur.execute("SELECT url, word_count, COALESCE(out_links,0) FROM pages")}

        # adjacency for neighbor outdeg avg
        adj = {}
        for u, v in links:
            adj.setdefault(u, []).append(v)

        import math
        def rhs(u):
            words = page_words.get(u, 0)
            outd = out_degree.get(u, 0)
            ind = in_degree.get(u, 0)
            neigh = adj.get(u, [])
            if neigh:
                avg_neigh_out = sum(out_degree.get(v, 0) for v in neigh) / len(neigh)
            else:
                avg_neigh_out = 0.0
            return (
                    0.40 * math.log1p(words) +
                    0.30 * math.log1p(outd) +
                    0.20 * math.log1p(avg_neigh_out) +
                    0.10 * math.log1p(ind)
            )

        scored = [(u, rhs(u)) for u in set(out_degree) | set(in_degree) | set(page_words)]
        scored.sort(key=lambda x: x[1], reverse=True)

        print("\n🕳️ Top 10 Rabbit-Hole pages:")
        for u, s in scored[:10]:
            print(
                f"  - {u}  RHS={s:.3f}  (words={page_words.get(u, 0)}, out={out_degree.get(u, 0)}, in={in_degree.get(u, 0)})")