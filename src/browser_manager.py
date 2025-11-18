#!/usr/bin/env python3
"""Browser management for Playwright-based scraping."""
import asyncio
from playwright.async_api import async_playwright, Page, Browser, Response
from typing import Optional


class BrowserManager:
    """Manages browser lifecycle and page operations."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """
        Initialize browser manager.
        
        Args:
            headless: Whether to run browser in headless mode
            timeout: Default timeout for page operations in milliseconds
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    async def start(self):
        """Initialize browser and page."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        print(f"Browser started (headless={self.headless})")
    
    async def close(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()
        print("Browser closed")
    
    async def navigate(self, url: str) -> Optional[Response]:
        """
        Navigate to a URL.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Response object or None
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        return await self.page.goto(url, wait_until="networkidle", timeout=self.timeout)
    
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None):
        """
        Wait for a selector to appear on the page.
        
        Args:
            selector: CSS selector to wait for
            timeout: Timeout in milliseconds (uses default if None)
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        await self.page.wait_for_selector(selector, timeout=timeout or self.timeout)
    
    async def query_selector(self, selector: str):
        """Query for a single element."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        return await self.page.query_selector(selector)
    
    async def query_selector_all(self, selector: str):
        """Query for all matching elements."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        return await self.page.query_selector_all(selector)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
