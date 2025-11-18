#!/usr/bin/env python3
"""AJAX form-based scraper using Playwright with async/await."""
import asyncio
from typing import List, Dict, Optional
from browser_manager import BrowserManager
from response_handler import ResponseHandler
from quote_parser import QuoteParser
from data_store import DataStore


class AjaxQuoteScraper:
    """Handles AJAX form-based scraping with form interactions."""
    
    def __init__(
        self,
        base_url: str,
        delay: float = 1.0,
        headless: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize the AJAX quote scraper.
        
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
    
    async def get_form_options(self, author: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get available options from the search form.
        
        Args:
            author: If provided, get tags available for this author
        
        Returns:
            Dictionary with authors and tags available in the form
        """
        await self.browser.navigate(self.base_url)
        
        # Wait for form to load
        await self.browser.wait_for_selector('select#author', timeout=10000)
        
        # Get author options
        author_options = await self.browser.page.evaluate('''
            () => {
                const select = document.querySelector('select#author');
                const options = Array.from(select.options);
                return options.slice(1).map(opt => opt.value); // Skip first "----------" option
            }
        ''')
        
        # Get tag options (may depend on author selection)
        tag_options = []
        if author:
            # Select author to trigger tag loading
            await self.browser.page.select_option('select#author', author)
            # Wait for tags to load via AJAX
            await asyncio.sleep(1)
            tag_options = await self.browser.page.evaluate('''
                () => {
                    const select = document.querySelector('select#tag');
                    const options = Array.from(select.options);
                    return options.slice(1).map(opt => opt.value); // Skip first "----------" option
                }
            ''')
        
        return {
            'authors': author_options,
            'tags': tag_options
        }
    
    async def search_quotes(
        self,
        author: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for quotes using the AJAX form.
        
        Args:
            author: Author name to filter by
            tag: Tag to filter by
            
        Returns:
            List of quotes matching the criteria
        """
        # Navigate to the search page
        await self.browser.navigate(self.base_url)
        
        # Wait for form to load
        await self.browser.wait_for_selector('form', timeout=10000)
        
        # Fill out form fields
        if author:
            await self.browser.page.select_option('select#author', author)
            print(f"  Selected author: {author}")
            await asyncio.sleep(0.5)
        
        if tag:
            await self.browser.page.select_option('select#tag', tag)
            print(f"  Selected tag: {tag}")
            await asyncio.sleep(0.5)
        
        # Click the search button
        await self.browser.page.click('input[type="submit"]')
        print("  Submitted search form")
        
        # Wait for results to load (AJAX response)
        # The form uses __VIEWSTATE, so we need to wait for the page to update
        await asyncio.sleep(2)
        
        # Check if quotes are present
        quote_elements = await self.browser.query_selector_all('.quote')
        if not quote_elements:
            print("  ⚠ No quotes found for the search criteria")
            return []
        
        # Extract quotes
        quotes = await self.parser.parse_quotes(quote_elements)
        
        print(f"  Found {len(quotes)} quotes")
        
        return quotes
    
    async def scrape_by_all_authors(self) -> Dict[str, List[Dict]]:
        """
        Scrape quotes for all available authors.
        
        Returns:
            Dictionary mapping author names to their quotes
        """
        options = await self.get_form_options()
        authors = options['authors']
        
        print(f"Found {len(authors)} authors to scrape\n")
        
        results = {}
        for i, author in enumerate(authors, 1):
            print(f"[{i}/{len(authors)}] Scraping author: {author}")
            quotes = await self.search_quotes(author=author)
            results[author] = quotes
            await asyncio.sleep(self.delay)
        
        return results
    
    async def scrape_by_all_tags(self) -> Dict[str, List[Dict]]:
        """
        Scrape quotes for all available tags.
        
        Returns:
            Dictionary mapping tag names to their quotes
        """
        options = await self.get_form_options()
        tags = options['tags']
        
        print(f"Found {len(tags)} tags to scrape\n")
        
        results = {}
        for i, tag in enumerate(tags, 1):
            print(f"[{i}/{len(tags)}] Scraping tag: {tag}")
            quotes = await self.search_quotes(tag=tag)
            results[tag] = quotes
            await asyncio.sleep(self.delay)
        
        return results
    
    def save_quotes(self, quotes: List[Dict], filename: str):
        """Save quotes to JSON file."""
        self.data_store.save_to_json(quotes, filename)


async def main():
    """Example usage of AJAX scraper."""
    url = "https://quotes.toscrape.com/search.aspx"
    
    print(f"AJAX Form-Based Scraper")
    print(f"URL: {url}\n")
    
    # Create scraper and start browser
    scraper = AjaxQuoteScraper(base_url=url, delay=0.5, headless=True)
    await scraper.start()
    
    try:
        # Get available form options
        print("=" * 60)
        print("Getting form options...")
        print("=" * 60)
        options = await scraper.get_form_options()
        print(f"Authors: {len(options['authors'])}")
        print(f"Sample authors: {', '.join(options['authors'][:5])}...")
        
        # Get tags for a specific author
        options_with_tags = await scraper.get_form_options(author="Albert Einstein")
        print(f"\nTags for 'Albert Einstein': {len(options_with_tags['tags'])}")
        if options_with_tags['tags']:
            print(f"Sample tags: {', '.join(options_with_tags['tags'][:10])}...")
        
        # Example 1: Search by author and tag
        print("\n" + "=" * 60)
        print("Example 1: Search by author 'Albert Einstein' and tag 'inspirational'")
        print("=" * 60)
        einstein_quotes = await scraper.search_quotes(author="Albert Einstein", tag="inspirational")
        
        print("\n" + "=" * 60)
        print("Sample Einstein Quotes:")
        print("=" * 60)
        for i, quote in enumerate(einstein_quotes[:3], 1):
            print(f"\n{i}. {quote['text']}")
            print(f"   - {quote['author']}")
            print(f"   Tags: {', '.join(quote['tags'])}")
        
        scraper.save_quotes(einstein_quotes, "quotes_einstein.json")
        
        # Example 2: Search by author and tag
        print("\n\n" + "=" * 60)
        print("Example 2: Search by author 'J.K. Rowling' and tag 'abilities'")
        print("=" * 60)
        jk_quotes = await scraper.search_quotes(author="J.K. Rowling", tag="abilities")
        
        print("\n" + "=" * 60)
        print("Sample J.K. Rowling Quotes:")
        print("=" * 60)
        for i, quote in enumerate(jk_quotes[:2], 1):
            print(f"\n{i}. {quote['text']}")
            print(f"   - {quote['author']}")
            print(f"   Tags: {', '.join(quote['tags'])}")
        
        scraper.save_quotes(jk_quotes, "quotes_jk_ajax.json")
        
    finally:
        # Close browser when done
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
