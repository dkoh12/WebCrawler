"""
Web Crawler Module

A simple web crawler that discovers and visits URLs starting from a seed URL.
Supports breadth-first crawling with domain restrictions.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque
import time


class WebCrawler:
    """
    A web crawler that discovers and visits URLs starting from a seed URL.
    
    Attributes:
        seed_url (str): The starting URL for crawling
        max_pages (int): Maximum number of pages to crawl
        delay (float): Delay between requests in seconds
        visited (set): Set of visited URLs
        to_visit (deque): Queue of URLs to visit
        same_domain_only (bool): Whether to restrict crawling to the same domain
    """
    
    def __init__(self, seed_url, max_pages=50, delay=1.0, same_domain_only=True):
        """
        Initialize the web crawler.
        
        Args:
            seed_url (str): The starting URL for crawling
            max_pages (int): Maximum number of pages to crawl (default: 50)
            delay (float): Delay between requests in seconds (default: 1.0)
            same_domain_only (bool): Restrict crawling to same domain (default: True)
        """
        self.seed_url = seed_url
        self.max_pages = max_pages
        self.delay = delay
        self.same_domain_only = same_domain_only
        self.visited = set()
        self.to_visit = deque([seed_url])
        self.domain = urlparse(seed_url).netloc
        
    def is_valid_url(self, url):
        """
        Check if a URL is valid for crawling.
        
        Args:
            url (str): The URL to validate
            
        Returns:
            bool: True if the URL is valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False
            
            if self.same_domain_only and parsed.netloc != self.domain:
                return False
                
            return True
        except Exception:
            return False
    
    def extract_links(self, html, base_url):
        """
        Extract all links from HTML content.
        
        Args:
            html (str): The HTML content to parse
            base_url (str): The base URL for resolving relative links
            
        Returns:
            set: A set of absolute URLs found in the HTML
        """
        links = set()
        try:
            soup = BeautifulSoup(html, 'html.parser')
            for anchor in soup.find_all('a', href=True):
                href = anchor['href']
                absolute_url = urljoin(base_url, href)
                # Remove fragment identifiers
                absolute_url = absolute_url.split('#')[0]
                if self.is_valid_url(absolute_url):
                    links.add(absolute_url)
        except Exception as e:
            print(f"Error extracting links: {e}")
        
        return links
    
    def fetch_page(self, url):
        """
        Fetch a web page and return its content.
        
        Args:
            url (str): The URL to fetch
            
        Returns:
            str: The HTML content of the page, or None if fetch failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; WebCrawler/1.0)'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def crawl(self):
        """
        Start the crawling process.
        
        Returns:
            list: A list of visited URLs
        """
        print(f"Starting crawl from {self.seed_url}")
        print(f"Max pages: {self.max_pages}, Delay: {self.delay}s")
        print(f"Same domain only: {self.same_domain_only}")
        print("-" * 50)
        
        while self.to_visit and len(self.visited) < self.max_pages:
            url = self.to_visit.popleft()
            
            if url in self.visited:
                continue
            
            print(f"Crawling [{len(self.visited) + 1}/{self.max_pages}]: {url}")
            
            html = self.fetch_page(url)
            if html:
                self.visited.add(url)
                links = self.extract_links(html, url)
                
                # Add new links to the queue
                for link in links:
                    if link not in self.visited and link not in self.to_visit:
                        self.to_visit.append(link)
                
                print(f"  Found {len(links)} links")
                
                # Polite delay between requests
                if self.to_visit:
                    time.sleep(self.delay)
            else:
                print(f"  Failed to fetch page")
        
        print("-" * 50)
        print(f"Crawl complete. Visited {len(self.visited)} pages.")
        
        return list(self.visited)
    
    def get_statistics(self):
        """
        Get crawling statistics.
        
        Returns:
            dict: Statistics about the crawl
        """
        return {
            'visited_count': len(self.visited),
            'queue_size': len(self.to_visit),
            'visited_urls': list(self.visited)
        }


if __name__ == "__main__":
    # Example usage
    crawler = WebCrawler(
        seed_url="https://example.com",
        max_pages=10,
        delay=1.0,
        same_domain_only=True
    )
    
    visited_urls = crawler.crawl()
    
    print("\nVisited URLs:")
    for url in visited_urls:
        print(f"  - {url}")
