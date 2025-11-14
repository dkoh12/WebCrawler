#!/usr/bin/env python3
"""
Example script demonstrating how to use the WebCrawler class.
"""

from web_crawler import WebCrawler


def main():
    """Run a simple crawling example."""
    print("=" * 60)
    print("Web Crawler Example")
    print("=" * 60)
    print()
    
    # Example 1: Crawl a small website
    print("Example 1: Crawling example.com with default settings")
    print()
    
    crawler = WebCrawler(
        seed_url="https://example.com",
        max_pages=10,
        delay=1.0,
        same_domain_only=True
    )
    
    visited_urls = crawler.crawl()
    
    print()
    print(f"Total pages visited: {len(visited_urls)}")
    print()
    
    # Get statistics
    stats = crawler.get_statistics()
    print("Crawl Statistics:")
    print(f"  - Pages visited: {stats['visited_count']}")
    print(f"  - URLs in queue: {stats['queue_size']}")
    print()
    
    print("Visited URLs:")
    for i, url in enumerate(visited_urls, 1):
        print(f"  {i}. {url}")
    
    print()
    print("=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
