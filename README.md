# WebCrawler

A simple and efficient web crawler written in Python that discovers and visits URLs starting from a seed URL.

## Features

- **Breadth-First Crawling**: Discovers web pages level by level
- **Domain Restriction**: Option to restrict crawling to the same domain
- **Polite Crawling**: Configurable delays between requests
- **Link Extraction**: Automatically extracts and follows links from HTML pages
- **Error Handling**: Robust error handling for network issues
- **Statistics**: Track visited pages and crawling progress

## Installation

1. Clone the repository:
```bash
git clone https://github.com/dkoh12/WebCrawler.git
cd WebCrawler
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from web_crawler import WebCrawler

# Create a crawler instance
crawler = WebCrawler(
    seed_url="https://example.com",
    max_pages=50,
    delay=1.0,
    same_domain_only=True
)

# Start crawling
visited_urls = crawler.crawl()

# Print results
print(f"Visited {len(visited_urls)} pages")
for url in visited_urls:
    print(url)
```

### Run Example Script

```bash
python example.py
```

### Command-Line Usage

```bash
python web_crawler.py
```

## Configuration Options

- `seed_url` (str): The starting URL for crawling
- `max_pages` (int): Maximum number of pages to crawl (default: 50)
- `delay` (float): Delay between requests in seconds (default: 1.0)
- `same_domain_only` (bool): Restrict crawling to the same domain (default: True)

## Example

```python
from web_crawler import WebCrawler

# Crawl up to 100 pages with 2-second delay
crawler = WebCrawler(
    seed_url="https://example.com",
    max_pages=100,
    delay=2.0,
    same_domain_only=True
)

visited_urls = crawler.crawl()

# Get statistics
stats = crawler.get_statistics()
print(f"Visited: {stats['visited_count']} pages")
print(f"Queue size: {stats['queue_size']}")
```

## Requirements

- Python 3.7+
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- urllib3 >= 2.0.6

## License

See LICENSE file for details.
