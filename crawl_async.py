#!/usr/bin/env python3
import asyncio
import httpx
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Set, List, Optional
from collections import deque
import time
import random


class AsyncWebCrawler:
    def __init__(self, max_pages: int = 50, delay: float = 1.0, max_concurrent: int = 10):
        """
        Initialize the async web crawler.
        
        Args:
            max_pages: Maximum number of pages to crawl
            delay: Delay between batches in seconds
            max_concurrent: Maximum number of concurrent requests
        """
        self.max_pages = max_pages
        self.delay = delay
        self.max_concurrent = max_concurrent
        self.visited_urls: Set[str] = set()
        self.files_found: Set[str] = set()  # Track non-HTML files
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self.current_user_agent = self.user_agents[0]
        self.robot_parser = RobotFileParser()
        self.max_retries = 3
        self.retry_delay_base = 2  # Base delay for exponential backoff
        self.semaphore = asyncio.Semaphore(max_concurrent)  # Limit concurrent requests
    
    def rotate_user_agent(self) -> None:
        """Rotate to a different user agent."""
        self.current_user_agent = random.choice(self.user_agents)
        print(f"  ↻ Rotated user agent")
    
    async def load_robots_txt(self, base_url: str) -> None:
        """
        Load and parse the robots.txt file for the domain.
        
        Args:
            base_url: Base URL of the website
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            # RobotFileParser.read() is synchronous, so we use it directly
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            print(f"Loaded robots.txt from: {robots_url}")
        except Exception as e:
            print(f"Could not load robots.txt: {e}")
            print("Proceeding without robots.txt restrictions")
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """
        Check if URL is valid and belongs to the same domain.
        Also filters out non-HTML files.
        
        Args:
            url: URL to validate
            base_domain: Base domain to restrict crawling
            
        Returns:
            True if URL is valid, on same domain, and is an HTML page
        """
        parsed = urlparse(url)
        
        # Must have a domain and match base domain
        if not (bool(parsed.netloc) and parsed.netloc == base_domain):
            return False
        
        # Skip non-HTML files
        skip_extensions = ('.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico',
                          '.zip', '.tar', '.gz', '.rar', '.7z',
                          '.mp3', '.mp4', '.avi', '.mov', '.wmv',
                          '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                          '.xml', '.json', '.csv', '.txt',
                          '.css', '.js', '.woff', '.woff2', '.ttf', '.eot')
        
        if url.lower().endswith(skip_extensions):
            self.files_found.add(url)
            return False
        
        return True
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if the URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL can be fetched
        """
        return self.robot_parser.can_fetch(self.current_user_agent, url)
    
    async def fetch_with_retry(self, client: httpx.AsyncClient, url: str, 
                               timeout: int = 10, retry_count: int = 0) -> Optional[httpx.Response]:
        """
        Fetch URL with retry logic and exponential backoff.
        
        Args:
            client: httpx AsyncClient instance
            url: URL to fetch
            timeout: Request timeout in seconds
            retry_count: Current retry attempt
            
        Returns:
            Response object if successful, None otherwise
        """
        try:
            # Semaphore ensures we don't exceed max_concurrent requests
            async with self.semaphore:
                response = await client.get(url, timeout=timeout)
            
            # 200: Success
            if response.status_code == 200:
                return response
            
            # 301/302: Redirect (httpx follows automatically)
            elif response.status_code in [301, 302]:
                print(f"  → Redirected to: {response.url}")
                return response
            
            # 404: Page not found - skip, log, don't retry
            elif response.status_code == 404:
                print(f"  ✗ Not Found (404): Skipping")
                return None
            
            # 403/401: Forbidden/Unauthorized - rotate user agent and retry
            elif response.status_code in [403, 401]:
                if retry_count < self.max_retries:
                    print(f"  ⚠ {response.status_code}: Rotating user agent and retrying...")
                    self.rotate_user_agent()
                    await asyncio.sleep(1)
                    return await self.fetch_with_retry(client, url, timeout, retry_count + 1)
                else:
                    print(f"  ✗ {response.status_code}: Max retries reached")
                    return None
            
            # 429: Too Many Requests - exponential backoff with jitter
            elif response.status_code == 429:
                if retry_count < self.max_retries:
                    backoff = (self.retry_delay_base ** retry_count) + random.uniform(0, 1)
                    print(f"  ⚠ 429: Rate limited, backing off for {backoff:.1f}s...")
                    await asyncio.sleep(backoff)
                    return await self.fetch_with_retry(client, url, timeout, retry_count + 1)
                else:
                    print(f"  ✗ 429: Max retries reached")
                    return None
            
            # 500/503: Server errors - retry with backoff (up to 3x)
            elif response.status_code in [500, 503]:
                if retry_count < self.max_retries:
                    backoff = self.retry_delay_base ** retry_count
                    print(f"  ⚠ {response.status_code}: Server error, retrying in {backoff}s... (attempt {retry_count + 1}/{self.max_retries})")
                    await asyncio.sleep(backoff)
                    return await self.fetch_with_retry(client, url, timeout, retry_count + 1)
                else:
                    print(f"  ✗ {response.status_code}: Max retries reached")
                    return None
            
            else:
                print(f"  ? Unexpected status code: {response.status_code}")
                return None
        
        except httpx.TimeoutException:
            # Timeout - retry with longer timeout
            if retry_count < self.max_retries:
                new_timeout = timeout + 5
                print(f"  ⚠ Timeout: Retrying with {new_timeout}s timeout... (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(1)
                return await self.fetch_with_retry(client, url, new_timeout, retry_count + 1)
            else:
                print(f"  ✗ Timeout: Max retries reached")
                return None
        
        except httpx.ConnectError:
            # Connection error - retry with backoff
            if retry_count < self.max_retries:
                backoff = self.retry_delay_base ** retry_count
                print(f"  ⚠ Connection Error: Retrying in {backoff}s... (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(backoff)
                return await self.fetch_with_retry(client, url, timeout, retry_count + 1)
            else:
                print(f"  ✗ Connection Error: Max retries reached")
                return None
        
        except httpx.HTTPError as e:
            print(f"  ✗ Error: {e}")
            return None
    
    async def get_links(self, client: httpx.AsyncClient, url: str, base_domain: str) -> List[str]:
        """
        Extract all links from a webpage.
        
        Args:
            client: httpx AsyncClient instance
            url: URL to extract links from
            base_domain: Base domain to filter links
            
        Returns:
            List of valid URLs found on the page
        """
        response = await self.fetch_with_retry(client, url)
        
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Remove fragments
            absolute_url = absolute_url.split('#')[0]
            
            # is_valid_url handles domain check AND file filtering
            if self.is_valid_url(absolute_url, base_domain):
                links.append(absolute_url)
        
        return links
    
    async def crawl_url(self, client: httpx.AsyncClient, url: str, base_domain: str) -> List[str]:
        """
        Crawl a single URL and return its links.
        
        Args:
            client: httpx AsyncClient instance
            url: URL to crawl
            base_domain: Base domain for filtering
            
        Returns:
            List of links found on the page
        """
        print(f"Crawling: {url}")
        links = await self.get_links(client, url, base_domain)
        return links
    
    async def crawl(self, start_url: str) -> Set[str]:
        """
        Crawl website starting from the given URL using async/await.
        
        Args:
            start_url: URL to start crawling from
            
        Returns:
            Set of all visited URLs
        """
        base_domain = urlparse(start_url).netloc
        to_visit = deque([start_url])
        
        print(f"Starting async crawl from: {start_url}")
        print(f"Base domain: {base_domain}")
        print(f"Max pages: {self.max_pages}")
        print(f"Max concurrent requests: {self.max_concurrent}")
        
        # Load robots.txt
        await self.load_robots_txt(start_url)
        print()
        
        # Create httpx client with custom headers
        async with httpx.AsyncClient(
            headers={'User-Agent': self.current_user_agent},
            follow_redirects=True
        ) as client:
            
            while to_visit and len(self.visited_urls) < self.max_pages:
                # Prepare batch of URLs to crawl
                batch = []
                batch_size = min(self.max_concurrent, len(to_visit), 
                               self.max_pages - len(self.visited_urls))
                
                for _ in range(batch_size):
                    if to_visit:
                        url = to_visit.popleft()
                        
                        if url not in self.visited_urls and self.can_fetch(url):
                            self.visited_urls.add(url)
                            batch.append(url)
                
                if not batch:
                    break
                
                # Crawl batch concurrently
                tasks = [self.crawl_url(client, url, base_domain) for url in batch]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        print(f"Error crawling {batch[i]}: {result}")
                    else:
                        # Add new links to queue
                        for link in result:
                            if link not in self.visited_urls and link not in to_visit:
                                to_visit.append(link)
                
                # Rate limiting between batches
                await asyncio.sleep(self.delay)
        
        print(f"\nCrawling complete! Visited {len(self.visited_urls)} pages.")
        if self.files_found:
            print(f"Found {len(self.files_found)} non-HTML files (not crawled)")
        return self.visited_urls


async def main():
    # Test websites for web scraping practice
    test_sites = [
        "https://books.toscrape.com/",
        "https://quotes.toscrape.com/",
        "https://www.scrapingcourse.com/",
        "https://webscraper.io/test-sites"
    ]
    
    # Choose which site to crawl (change index to test different sites)
    start_url = test_sites[0]
    
    # max_concurrent controls how many requests happen at once
    crawler = AsyncWebCrawler(max_pages=20, delay=1.0, max_concurrent=10)
    visited_urls = await crawler.crawl(start_url)
    
    # Print results
    print("\n" + "="*50)
    print("Crawled URLs:")
    print("="*50)
    for i, url in enumerate(sorted(visited_urls), 1):
        print(f"{i}. {url}")
    
    # Print found files
    if crawler.files_found:
        print("\n" + "="*50)
        print("Non-HTML Files Found (not crawled):")
        print("="*50)
        for i, file_url in enumerate(sorted(crawler.files_found), 1):
            print(f"{i}. {file_url}")


if __name__ == "__main__":
    asyncio.run(main())
