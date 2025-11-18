#!/usr/bin/env python3
"""Modular web scraper using Playwright with async/await."""
import asyncio
from typing import List, Dict, Optional
from collections import deque
from browser_manager import BrowserManager
from response_handler import ResponseHandler
from quote_parser import QuoteParser
from data_store import DataStore


class QuoteScraper:
    """Orchestrates scraping using modular components."""
    
    def __init__(
        self,
        base_url: str,
        delay: float = 1.0,
        headless: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize the quote scraper.
        
        Args:
            base_url: Starting URL for scraping
            delay: Delay between requests in seconds
            headless: Whether to run browser in headless mode
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url
        self.delay = delay
        self.browser = BrowserManager(headless=headless)
        self.response_handler = ResponseHandler(max_retries=max_retries)
        self.parser = QuoteParser()
        self.data_store = DataStore()
        self._browser_started = False
    
    async def start(self):
        """Start the browser. Call once before scraping."""
        if not self._browser_started:
            await self.browser.start()
            self._browser_started = True
    
    async def close(self):
        """Close the browser. Call when done with all scraping."""
        if self._browser_started:
            await self.browser.close()
            self._browser_started = False
    
    async def scrape_page(self, url: str, retry_count: int = 0, use_scroll: bool = False) -> tuple[List[Dict], Optional[str]]:
        """
        Scrape a single page.
        
        Args:
            url: URL to scrape
            retry_count: Current retry attempt
            use_scroll: Whether to use infinite scroll instead of pagination
            
        Returns:
            Tuple of (quotes list, next page URL)
        """
        # Navigate to page
        response = await self.browser.navigate(url)
        
        # Handle response status
        is_ok = await self.response_handler.handle_response(
            response, 
            url,
            retry_callback=lambda rc: self.scrape_page(url, rc, use_scroll),
            retry_count=retry_count
        )
        
        if not is_ok:
            return [], None
        
        # Wait for content to load
        await self.browser.wait_for_selector('.quote', timeout=10000)
        
        # If using scroll, scroll to load all content
        if use_scroll:
            scroll_count = await self.browser.scroll_to_bottom(pause_time=1.0, max_scrolls=10)
            print(f"  Scrolled {scroll_count} times to load content")
        
        # Extract quotes
        quote_elements = await self.browser.query_selector_all('.quote')
        quotes = await self.parser.parse_quotes(quote_elements)
        
        # Extract next page URL (only if not using scroll)
        next_url = None if use_scroll else await self.parser.extract_next_page_url(
            self.browser.page, self.base_url
        )
        
        return quotes, next_url
    
    async def scrape_all(
        self,
        max_pages: Optional[int] = None,
        max_concurrent: int = 5,
        use_scroll: bool = False
    ) -> List[Dict]:
        """
        Scrape all pages in parallel.
        
        Args:
            max_pages: Maximum number of pages to scrape
            max_concurrent: Maximum concurrent page scrapes
            use_scroll: Whether to use infinite scroll instead of pagination
            
        Returns:
            List of all quotes
        """
        all_quotes = []
        visited_urls = set()
        to_visit = deque([self.base_url])
        page_count = 0
        semaphore = asyncio.Semaphore(max_concurrent)
        lock = asyncio.Lock()
        
        print(f"Starting {'scroll' if use_scroll else 'parallel'} scrape from: {self.base_url}")
        print(f"Max pages: {max_pages if max_pages else 'All'}")
        print(f"Max concurrent: {max_concurrent}")
        print()
        
        async def scrape_url_task(url: str):
            """Task to scrape a single URL with concurrency control."""
            async with semaphore:
                print(f"Scraping: {url}")
                quotes, next_url = await self.scrape_page(url, use_scroll=use_scroll)
                
                async with lock:
                    all_quotes.extend(quotes)
                    print(f"  Found {len(quotes)} quotes | Total: {len(all_quotes)}")
                    
                    if next_url and next_url not in visited_urls and next_url not in to_visit:
                        to_visit.append(next_url)
                
                await asyncio.sleep(self.delay)
        
        while to_visit and (max_pages is None or page_count < max_pages):
            # Prepare batch
            batch_size = min(
                max_concurrent,
                len(to_visit),
                (max_pages - page_count) if max_pages else len(to_visit)
            )
            
            batch = []
            for _ in range(batch_size):
                if to_visit:
                    url = to_visit.popleft()
                    if url not in visited_urls:
                        visited_urls.add(url)
                        batch.append(url)
                        page_count += 1
            
            if not batch:
                break
            
            # Scrape batch in parallel
            tasks = [scrape_url_task(url) for url in batch]
            await asyncio.gather(*tasks)
        
        print(f"\nScraping complete!")
        print(f"Total pages scraped: {page_count}")
        print(f"Total quotes collected: {len(all_quotes)}")
        
        return all_quotes
    
    async def scrape_by_tag(self, tag: str) -> List[Dict]:
        """
        Scrape quotes filtered by tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of quotes with the tag
        """
        url = f"{self.base_url}/tag/{tag}/"
        print(f"Scraping quotes with tag: '{tag}'")
        print(f"URL: {url}\n")
        
        all_quotes = []
        current_url = url
        page_count = 0
        
        while current_url:
            page_count += 1
            print(f"Scraping page {page_count}: {current_url}")
            
            quotes, next_url = await self.scrape_page(current_url)
            all_quotes.extend(quotes)
            
            print(f"  Found {len(quotes)} quotes on this page")
            
            current_url = next_url
            if current_url:
                await asyncio.sleep(self.delay)
        
        print(f"\nTotal quotes with tag '{tag}': {len(all_quotes)}")
        return all_quotes
    
    def save_quotes(self, quotes: List[Dict], filename: str):
        """Save quotes to JSON file."""
        self.data_store.save_to_json(quotes, filename)


async def main():
    """Example usage of modular scraper."""
    # List of available URLs
    urls = [
        "https://quotes.toscrape.com/",
        "https://quotes.toscrape.com/scroll",
        "https://quotes.toscrape.com/js/",
        "https://quotes.toscrape.com/js-delayed/",
        "https://quotes.toscrape.com/tableful/",
        "https://quotes.toscrape.com/login",
        "https://quotes.toscrape.com/search.aspx",
        "https://quotes.toscrape.com/random"
    ]
    
    seed_url = urls[1]
    print(f"Available URLs: {len(urls)}")
    print(f"Using seed URL: {seed_url}\n")
    
    # Create scraper and start browser once
    scraper = QuoteScraper(base_url=seed_url, delay=1.0, headless=True)
    await scraper.start()
    
    try:
        # Example 1: Scrape all quotes (with scroll for infinite scroll pages)
        print("=" * 60)
        print("Example 1: Scraping all quotes with infinite scroll")
        print("=" * 60)
        # Detect if URL uses scroll by checking if 'scroll' is in the URL
        use_scroll = 'scroll' in seed_url
        all_quotes = await scraper.scrape_all(max_pages=1, max_concurrent=1, use_scroll=use_scroll)
        
        # Print stats
        print("\n" + "=" * 60)
        print("Statistics:")
        print("=" * 60)
        authors = DataStore.get_authors(all_quotes)
        print(f"Unique authors: {len(authors)}")
        print(f"Authors: {', '.join(authors[:5])}...")
        
        all_tags = DataStore.get_all_tags(all_quotes)
        print(f"\nUnique tags: {len(all_tags)}")
        print(f"Tags: {', '.join(all_tags[:10])}...")
        
        # Print sample quotes
        print("\n" + "=" * 60)
        print("Sample Quotes:")
        print("=" * 60)
        for i, quote in enumerate(all_quotes[:3], 1):
            print(f"\n{i}. {quote['text']}")
            print(f"   - {quote['author']}")
            print(f"   Tags: {', '.join(quote['tags'])}")
        
        # Save to JSON
        scraper.save_quotes(all_quotes, "quotes_all.json")
        
        # Example 2: Scrape by tag (reusing same browser!)
        print("\n\n" + "=" * 60)
        print("Example 2: Scraping quotes with 'love' tag (reusing browser)")
        print("=" * 60)
        love_quotes = await scraper.scrape_by_tag('love')
        
        print("\n" + "=" * 60)
        print("Sample Love Quotes:")
        print("=" * 60)
        for i, quote in enumerate(love_quotes[:2], 1):
            print(f"\n{i}. {quote['text']}")
            print(f"   - {quote['author']}")
        
        scraper.save_quotes(love_quotes, "quotes_love.json")
        
    finally:
        # Close browser once when done with all scraping
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
