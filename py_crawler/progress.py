# py_crawler/progress.py

from rich.console import Console
from rich.table import Table
from rich.live import Live
from time import time, sleep
from threading import Thread, Lock


class CrawlStats:
    def __init__(self, topics=None, max_depth=None):
        self.console = Console()
        self.lock = Lock()
        self.start_time = time()

        self.pages_crawled = 0
        self.pages_queued = 0
        self.pages_failed = 0
        self.current_depth = 0
        self.max_depth = max_depth or 0
        self.retries = 0
        self.topics = topics or []

        self._running = True
        self._thread = Thread(target=self._live_render_loop, daemon=True)
        self._thread.start()

    def _render_table(self):
        with self.lock:
            elapsed = int(time() - self.start_time)
            mins, secs = divmod(elapsed, 60)

            table = Table(title="📊 Wikipedia Crawler Dashboard", expand=True)
            table.add_column("Metric", justify="left", style="cyan", no_wrap=True)
            table.add_column("Value", justify="right", style="magenta")

            table.add_row("Pages Crawled", str(self.pages_crawled))
            table.add_row("Pages Queued", str(self.pages_queued))
            table.add_row("Pages Failed", str(self.pages_failed))
            table.add_row("Current Depth", str(self.current_depth))
            table.add_row("Max Depth", str(self.max_depth))
            table.add_row("Retries", str(self.retries))
            table.add_row("Elapsed Time", f"{mins}m {secs}s")
            table.add_row("Topic Filter", ", ".join(self.topics) if self.topics else "None")

            return table

    def _live_render_loop(self):
        with Live(self._render_table(), refresh_per_second=0.5, console=self.console, transient=False, screen=False) as live:
            while self._running:
                sleep(1)
                live.update(self._render_table())

    def update(self, *, crawled=0, queued=0, failed=0, retries=0, depth=None):
        with self.lock:
            self.pages_crawled += crawled
            self.pages_queued = queued
            self.pages_failed += failed
            self.retries += retries
            if depth is not None:
                self.current_depth = max(self.current_depth, depth)

    def stop(self):
        self._running = False
        self._thread.join()
