#!/usr/bin/env python3
"""HTTP response and error handling utilities."""
import asyncio
from playwright.async_api import Response
from typing import Optional, Callable, TypeVar, Any

T = TypeVar('T')


class ResponseHandler:
    """Handles HTTP responses and implements retry logic."""
    
    def __init__(self, max_retries: int = 3):
        """
        Initialize response handler.
        
        Args:
            max_retries: Maximum number of retry attempts
        """
        self.max_retries = max_retries
    
    async def handle_response(
        self, 
        response: Optional[Response], 
        url: str,
        retry_callback: Optional[Callable] = None,
        retry_count: int = 0
    ) -> bool:
        """
        Handle HTTP response status codes with retry logic.
        
        Args:
            response: Response object from page navigation
            url: URL being accessed
            retry_callback: Async function to call for retries
            retry_count: Current retry attempt
            
        Returns:
            True if response is OK, False otherwise
        """
        if not response:
            print(f"  ✗ No response received for: {url}")
            return False
        
        status = response.status
        
        # 200: Success
        if status == 200:
            return True
        
        # 404: Not Found
        elif status == 404:
            print(f"  ✗ 404 Not Found: {url}")
            return False
        
        # 403/401: Forbidden/Unauthorized
        elif status in [403, 401]:
            if retry_count < self.max_retries and retry_callback:
                print(f"  ⚠ {status}: Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(2)
                return await retry_callback(retry_count + 1)
            else:
                print(f"  ✗ {status}: Max retries reached")
                return False
        
        # 429: Rate Limited
        elif status == 429:
            if retry_count < self.max_retries and retry_callback:
                backoff = (2 ** retry_count) + 1
                print(f"  ⚠ 429: Rate limited, backing off for {backoff}s...")
                await asyncio.sleep(backoff)
                return await retry_callback(retry_count + 1)
            else:
                print(f"  ✗ 429: Max retries reached")
                return False
        
        # 500/503: Server Error
        elif status in [500, 503]:
            if retry_count < self.max_retries and retry_callback:
                backoff = 2 ** retry_count
                print(f"  ⚠ {status}: Server error, retrying in {backoff}s... (attempt {retry_count + 1}/{self.max_retries})")
                await asyncio.sleep(backoff)
                return await retry_callback(retry_count + 1)
            else:
                print(f"  ✗ {status}: Max retries reached")
                return False
        
        # Other status codes
        elif status >= 400:
            print(f"  ✗ HTTP {status}: {url}")
            return False
        
        return True
    
    async def with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Optional[T]:
        """
        Execute a function with retry logic.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
            
        Returns:
            Result from func or None on failure
        """
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if retry_count < self.max_retries:
                    print(f"  ↻ Error: {e}. Retrying... (attempt {retry_count + 1}/{self.max_retries})")
                    await asyncio.sleep(2 ** retry_count)
                    retry_count += 1
                else:
                    print(f"  ✗ Max retries reached after error: {e}")
                    return None
        
        return None
