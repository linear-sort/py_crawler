from setuptools import setup, find_packages

setup(
    name="py_crawler",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "requests",
        "beautifulsoup4"
    ],
    entry_points={
        "console_scripts": [
            "export-wiki = py_crawler.export:cli",
            "crawl-wiki = py_crawler.wiki_crawler:main"
        ]
    },
    author="Your Name",
    description="Wikipedia BFS crawler with SQLite storage",
    python_requires='>=3.7',
)
