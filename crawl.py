import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Set, List
from collections import deque
import time


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
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
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
    
    def get_links(self, url: str, base_domain: str) -> List[str]:
        """
        Extract all links from a webpage.
        
        Args:
            url: URL to extract links from
            base_domain: Base domain to filter links
            
        Returns:
            List of valid URLs found on the page
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
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
        
        except requests.exceptions.RequestException as e:
            print(f"Error crawling {url}: {e}")
            return []
    
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
        print(f"Max pages: {self.max_pages}\n")
        
        while to_visit and len(self.visited_urls) < self.max_pages:
            url = to_visit.popleft()
            
            if url in self.visited_urls:
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
