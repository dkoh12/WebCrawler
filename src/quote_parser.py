#!/usr/bin/env python3
"""HTML parsing and data extraction for quotes."""
from typing import List, Dict, Optional
from playwright.async_api import ElementHandle


class QuoteParser:
    """Parses HTML to extract quote data."""
    
    @staticmethod
    async def parse_quote(quote_elem: ElementHandle) -> Dict[str, any]:
        """
        Parse a single quote element.
        
        Args:
            quote_elem: Quote element handle
            
        Returns:
            Dictionary with quote data
        """
        # Extract quote text
        text_elem = await quote_elem.query_selector('.text')
        text = await text_elem.inner_text() if text_elem else ""
        
        # Extract author
        author_elem = await quote_elem.query_selector('.author')
        author = await author_elem.inner_text() if author_elem else ""
        
        # Extract tags
        tag_elements = await quote_elem.query_selector_all('.tag')
        tags = []
        for tag_elem in tag_elements:
            tag_text = await tag_elem.inner_text()
            tags.append(tag_text)
        
        return {
            'text': text,
            'author': author,
            'tags': tags
        }
    
    @staticmethod
    async def parse_quotes(quote_elements: List[ElementHandle]) -> List[Dict]:
        """
        Parse multiple quote elements.
        
        Args:
            quote_elements: List of quote element handles
            
        Returns:
            List of quote dictionaries
        """
        quotes = []
        for quote_elem in quote_elements:
            quote = await QuoteParser.parse_quote(quote_elem)
            quotes.append(quote)
        return quotes
    
    @staticmethod
    async def extract_next_page_url(page, base_url: str) -> Optional[str]:
        """
        Extract next page URL from pagination.
        
        Args:
            page: Playwright page object
            base_url: Base URL for constructing absolute URLs
            
        Returns:
            Next page URL or None
        """
        next_button = await page.query_selector('li.next > a')
        if next_button:
            href = await next_button.get_attribute('href')
            if href:
                # Handle both relative and absolute URLs
                if href.startswith('http'):
                    return href
                elif href.startswith('/'):
                    return base_url.rstrip('/') + href
                else:
                    return base_url.rstrip('/') + '/' + href
        return None
