#!/usr/bin/env python3
"""
Unit tests for the WebCrawler class.
"""

import unittest
from unittest.mock import patch, Mock
from web_crawler import WebCrawler


class TestWebCrawler(unittest.TestCase):
    """Test cases for the WebCrawler class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.crawler = WebCrawler(
            seed_url="https://example.com",
            max_pages=5,
            delay=0.1,
            same_domain_only=True
        )
    
    def test_initialization(self):
        """Test crawler initialization."""
        self.assertEqual(self.crawler.seed_url, "https://example.com")
        self.assertEqual(self.crawler.max_pages, 5)
        self.assertEqual(self.crawler.delay, 0.1)
        self.assertTrue(self.crawler.same_domain_only)
        self.assertEqual(len(self.crawler.visited), 0)
        self.assertEqual(len(self.crawler.to_visit), 1)
        self.assertEqual(self.crawler.domain, "example.com")
    
    def test_is_valid_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(self.crawler.is_valid_url("https://example.com/page"))
        self.assertTrue(self.crawler.is_valid_url("https://example.com/about"))
        
        # Invalid URLs - different domain (when same_domain_only is True)
        self.assertFalse(self.crawler.is_valid_url("https://other.com/page"))
        
        # Invalid URLs - malformed
        self.assertFalse(self.crawler.is_valid_url("not-a-url"))
        self.assertFalse(self.crawler.is_valid_url(""))
    
    def test_is_valid_url_cross_domain(self):
        """Test URL validation with cross-domain crawling enabled."""
        crawler = WebCrawler(
            seed_url="https://example.com",
            same_domain_only=False
        )
        
        # Should allow different domains
        self.assertTrue(crawler.is_valid_url("https://other.com/page"))
        self.assertTrue(crawler.is_valid_url("https://example.com/page"))
    
    def test_extract_links(self):
        """Test link extraction from HTML."""
        html = """
        <html>
            <body>
                <a href="https://example.com/page1">Link 1</a>
                <a href="/page2">Link 2</a>
                <a href="https://other.com/page">External Link</a>
                <a href="#fragment">Fragment</a>
            </body>
        </html>
        """
        
        links = self.crawler.extract_links(html, "https://example.com")
        
        # Should extract links from same domain
        self.assertIn("https://example.com/page1", links)
        self.assertIn("https://example.com/page2", links)
        
        # Should not include external links (same_domain_only=True)
        self.assertNotIn("https://other.com/page", links)
        
        # Should not include fragments
        self.assertNotIn("https://example.com#fragment", links)
    
    def test_extract_links_relative(self):
        """Test extraction of relative links."""
        html = """
        <html>
            <body>
                <a href="/about">About</a>
                <a href="contact">Contact</a>
                <a href="../home">Home</a>
            </body>
        </html>
        """
        
        links = self.crawler.extract_links(html, "https://example.com/foo/bar")
        
        # Check that relative URLs are properly converted to absolute
        self.assertIn("https://example.com/about", links)
        self.assertIn("https://example.com/foo/contact", links)
        self.assertIn("https://example.com/home", links)
    
    @patch('web_crawler.requests.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetching."""
        mock_response = Mock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        html = self.crawler.fetch_page("https://example.com")
        
        self.assertEqual(html, "<html><body>Test</body></html>")
        mock_get.assert_called_once()
    
    @patch('web_crawler.requests.get')
    def test_fetch_page_failure(self, mock_get):
        """Test page fetching with network error."""
        import requests
        mock_get.side_effect = requests.exceptions.RequestException("Network error")
        
        html = self.crawler.fetch_page("https://example.com")
        
        self.assertIsNone(html)
    
    @patch('web_crawler.requests.get')
    @patch('web_crawler.time.sleep')
    def test_crawl(self, mock_sleep, mock_get):
        """Test the crawling process."""
        # Mock responses for different pages
        responses = {
            "https://example.com": """
                <html><body>
                    <a href="/page1">Page 1</a>
                    <a href="/page2">Page 2</a>
                </body></html>
            """,
            "https://example.com/page1": """
                <html><body>
                    <a href="/page3">Page 3</a>
                </body></html>
            """,
            "https://example.com/page2": "<html><body>Page 2 content</body></html>",
            "https://example.com/page3": "<html><body>Page 3 content</body></html>"
        }
        
        def mock_get_response(url, **kwargs):
            mock_response = Mock()
            mock_response.text = responses.get(url, "<html></html>")
            mock_response.raise_for_status = Mock()
            return mock_response
        
        mock_get.side_effect = mock_get_response
        
        visited = self.crawler.crawl()
        
        # Should visit up to max_pages
        self.assertGreater(len(visited), 0)
        self.assertLessEqual(len(visited), self.crawler.max_pages)
        
        # Should visit the seed URL
        self.assertIn("https://example.com", visited)
    
    def test_get_statistics(self):
        """Test statistics retrieval."""
        self.crawler.visited.add("https://example.com")
        self.crawler.visited.add("https://example.com/page1")
        
        stats = self.crawler.get_statistics()
        
        self.assertEqual(stats['visited_count'], 2)
        self.assertIn('queue_size', stats)
        self.assertIn('visited_urls', stats)
        self.assertEqual(len(stats['visited_urls']), 2)


if __name__ == "__main__":
    unittest.main()
