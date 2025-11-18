#!/usr/bin/env python3
"""HTML parsing and data extraction for quotes."""
from typing import List, Dict, Optional
from playwright.async_api import ElementHandle


class QuoteParser:
    """Parses HTML to extract quote data."""
    
    def __init__(self, selectors: Optional[Dict[str, str]] = None):
        """
        Initialize quote parser.
        
        Args:
            selectors: Custom CSS selectors for quote elements
        """
        if selectors is not None:
            self.selectors = selectors
        else:
            self.selectors = {
                'text': '.text',
                'author': '.author',
                'tags': '.tag'
            }
    
    async def parse_quote(self, quote_elem: ElementHandle) -> Dict[str, any]:
        """
        Parse a single quote element.
        
        Args:
            quote_elem: Quote element handle
            
        Returns:
            Dictionary with quote data
        """
        # Check if we're using custom table-based parsing
        text_selector = self.selectors.get('text')
        
        if text_selector is None:
            # Table-based layout: parse from plain text
            full_text = await quote_elem.inner_text()
            
            # Extract quote and author from format: "Quote text" Author: Name
            text = ""
            author = ""
            
            # Split by "Author:" to separate quote and author
            if 'Author:' in full_text:
                parts = full_text.split(' Author: ')
                if len(parts) == 2:
                    text = parts[0].strip()
                    author = parts[1].strip()
            
            # Extract tags from next sibling row
            tags = []
            try:
                parent_row = await quote_elem.evaluate_handle('(el) => el.parentElement')
                if parent_row:
                    next_row = await parent_row.evaluate_handle('(el) => el.nextElementSibling')
                    if next_row:
                        tag_cell = await next_row.query_selector('td')
                        if tag_cell:
                            tag_links = await tag_cell.query_selector_all('a')
                            for tag_link in tag_links:
                                tag_text = await tag_link.inner_text()
                                tags.append(tag_text.strip())
            except Exception as e:
                pass
            
            return {
                'text': text,
                'author': author,
                'tags': tags
            }
        
        # Standard parsing with CSS selectors
        # Extract quote text
        text_elem = await quote_elem.query_selector(self.selectors['text'])
        text = await text_elem.inner_text() if text_elem else ""
        
        # Extract author
        author_elem = await quote_elem.query_selector(self.selectors['author'])
        author = await author_elem.inner_text() if author_elem else ""
        
        # Extract tags
        tag_elements = await quote_elem.query_selector_all(self.selectors['tags'])
        tags = []
        for tag_elem in tag_elements:
            tag_text = await tag_elem.inner_text()
            tags.append(tag_text)
        
        return {
            'text': text,
            'author': author,
            'tags': tags
        }
    
    async def parse_quotes(self, quote_elements: List[ElementHandle]) -> List[Dict]:
        """
        Parse multiple quote elements.
        
        Args:
            quote_elements: List of quote element handles
            
        Returns:
            List of quote dictionaries
        """
        quotes = []
        for quote_elem in quote_elements:
            quote = await self.parse_quote(quote_elem)
            quotes.append(quote)
        return quotes
    
    async def extract_next_page_url(self, page, base_url: str) -> Optional[str]:
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
                    # Extract domain from base_url for absolute paths
                    from urllib.parse import urlparse
                    parsed = urlparse(base_url)
                    return f"{parsed.scheme}://{parsed.netloc}{href}"
                else:
                    # Relative path - append to current page URL
                    return base_url.rstrip('/') + '/' + href
        return None
