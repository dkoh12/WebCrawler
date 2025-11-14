#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Set, List, Optional
from collections import deque
import time
import random


class WebCrawler:
    def __init__(self, max_pages: int = 50, delay: float = 1.0):
        """
        Initialize the web crawler.
        
        Args:
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
        """
        self.max_pages = max_pages
        self.delay = delay
        self.visited_urls: Set[str] = set()
        self.session = requests.Session()
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
        self.session.headers.update({
            'User-Agent': self.user_agents[0]
        })
        self.robot_parser = RobotFileParser()
        self.max_retries = 3
        self.retry_delay_base = 2  # Base delay for exponential backoff
    
    def rotate_user_agent(self) -> None:
        """Rotate to a different user agent."""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': user_agent})
        print(f"  ↻ Rotated user agent")
    
    def load_robots_txt(self, base_url: str) -> None:
        """
        Load and parse the robots.txt file for the domain.
        
        Args:
            base_url: Base URL of the website
        """
        parsed = urlparse(base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        
        try:
            self.robot_parser.set_url(robots_url)
            self.robot_parser.read()
            print(f"Loaded robots.txt from: {robots_url}")
        except Exception as e:
            print(f"Could not load robots.txt: {e}")
            print("Proceeding without robots.txt restrictions")
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """
        Check if URL is valid and belongs to the same domain.
        
        Args:
            url: URL to validate
            base_domain: Base domain to restrict crawling
            
        Returns:
            True if URL is valid and belongs to base domain
        """
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == base_domain
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if the URL can be fetched according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL can be fetched
        """
        user_agent = self.session.headers.get('User-Agent', '*')
        return self.robot_parser.can_fetch(user_agent, url)
    
    def fetch_with_retry(self, url: str, timeout: int = 10, retry_count: int = 0) -> Optional[requests.Response]:
        """
        Fetch URL with retry logic and exponential backoff.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            retry_count: Current retry attempt
            
        Returns:
            Response object if successful, None otherwise
        """
        try:
            response = self.session.get(url, timeout=timeout)
            
            # 200: Success
            if response.status_code == 200:
                return response
            
            # 301/302: Redirect (requests follows automatically)
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
                    time.sleep(1)
                    return self.fetch_with_retry(url, timeout, retry_count + 1)
                else:
                    print(f"  ✗ {response.status_code}: Max retries reached")
                    return None
            
            # 429: Too Many Requests - exponential backoff with jitter
            elif response.status_code == 429:
                if retry_count < self.max_retries:
                    backoff = (self.retry_delay_base ** retry_count) + random.uniform(0, 1)
                    print(f"  ⚠ 429: Rate limited, backing off for {backoff:.1f}s...")
                    time.sleep(backoff)
                    return self.fetch_with_retry(url, timeout, retry_count + 1)
                else:
                    print(f"  ✗ 429: Max retries reached")
                    return None
            
            # 500/503: Server errors - retry with backoff (up to 3x)
            elif response.status_code in [500, 503]:
                if retry_count < self.max_retries:
                    backoff = self.retry_delay_base ** retry_count
                    print(f"  ⚠ {response.status_code}: Server error, retrying in {backoff}s... (attempt {retry_count + 1}/{self.max_retries})")
                    time.sleep(backoff)
                    return self.fetch_with_retry(url, timeout, retry_count + 1)
                else:
                    print(f"  ✗ {response.status_code}: Max retries reached")
                    return None
            
            else:
                print(f"  ? Unexpected status code: {response.status_code}")
                return None
        
        except requests.exceptions.Timeout:
            # Timeout - retry with longer timeout
            if retry_count < self.max_retries:
                new_timeout = timeout + 5
                print(f"  ⚠ Timeout: Retrying with {new_timeout}s timeout... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(1)
                return self.fetch_with_retry(url, new_timeout, retry_count + 1)
            else:
                print(f"  ✗ Timeout: Max retries reached")
                return None
        
        except requests.exceptions.ConnectionError:
            # Connection error - retry with backoff
            if retry_count < self.max_retries:
                backoff = self.retry_delay_base ** retry_count
                print(f"  ⚠ Connection Error: Retrying in {backoff}s... (attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(backoff)
                return self.fetch_with_retry(url, timeout, retry_count + 1)
            else:
                print(f"  ✗ Connection Error: Max retries reached")
                return None
        
        except requests.exceptions.RequestException as e:
            print(f"  ✗ Error: {e}")
            return None
    
    def get_links(self, url: str, base_domain: str) -> List[str]:
        """
        Extract all links from a webpage.
        
        Args:
            url: URL to extract links from
            base_domain: Base domain to filter links
            
        Returns:
            List of valid URLs found on the page
        """
        response = self.fetch_with_retry(url)
        
        if response is None:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Remove fragments
            absolute_url = absolute_url.split('#')[0]
            
            if self.is_valid_url(absolute_url, base_domain):
                links.append(absolute_url)
        
        return links
    
    def crawl(self, start_url: str) -> Set[str]:
        """
        Crawl website starting from the given URL.
        
        Args:
            start_url: URL to start crawling from
            
        Returns:
            Set of all visited URLs
        """
        base_domain = urlparse(start_url).netloc
        to_visit = deque([start_url])
        
        print(f"Starting crawl from: {start_url}")
        print(f"Base domain: {base_domain}")
        print(f"Max pages: {self.max_pages}")
        
        # Load robots.txt
        self.load_robots_txt(start_url)
        print()
        
        while to_visit and len(self.visited_urls) < self.max_pages:
            url = to_visit.popleft()
            
            if url in self.visited_urls:
                continue
            
            # Check if we're allowed to crawl this URL
            if not self.can_fetch(url):
                print(f"Skipping (disallowed by robots.txt): {url}")
                continue
            
            print(f"Crawling [{len(self.visited_urls) + 1}/{self.max_pages}]: {url}")
            self.visited_urls.add(url)
            
            # Get links from current page
            links = self.get_links(url, base_domain)
            
            # Add new links to queue
            for link in links:
                if link not in self.visited_urls and link not in to_visit:
                    to_visit.append(link)
            
            # Respectful crawling - add delay
            time.sleep(self.delay)
        
        print(f"\nCrawling complete! Visited {len(self.visited_urls)} pages.")
        return self.visited_urls


def main():
    # Test websites for web scraping practice
    test_sites = [
        "https://books.toscrape.com/",
        "https://quotes.toscrape.com/",
        "https://www.scrapingcourse.com/",
        "https://webscraper.io/test-sites"
    ]
    
    # Choose which site to crawl (change index to test different sites)
    start_url = test_sites[0]
    
    crawler = WebCrawler(max_pages=20, delay=1.0)
    visited_urls = crawler.crawl(start_url)
    
    # Print results
    print("\n" + "="*50)
    print("Crawled URLs:")
    print("="*50)
    for i, url in enumerate(sorted(visited_urls), 1):
        print(f"{i}. {url}")


if __name__ == "__main__":
    main()
