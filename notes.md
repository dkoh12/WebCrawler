
https://scrape.do/blog/web-crawler-python/

Today, pages are built with JavaScript frameworks that render content only in the browser. Many sites are hidden behind login walls, use dynamic URLs, or load content via background AJAX calls.

And to protect themselves from scraping and abuse, sites now use:

Bot detection systems like Cloudflare and DataDome
Behavior analysis and TLS fingerprint checks
CAPTCHA walls and aggressive IP blocking
Geo-restrictions and rate-limiting based on traffic patterns

All of this means that requests.get() by itself is rarely enough. Modern crawlers need more than basic HTTP calls.

They need to mimic real browsers, rotate identities, respect site policies, and recover from failures automatically.

**Rate Limiting & Throttling**

If your crawler hits a website too quickly even politely and ethically you risk being flagged as a bot or triggering automated blocks. Web servers expect human-like timing: a few seconds between actions, not a barrage of requests per second.

add delays between requests and randomized backoff range.

**Rotating Headers, User Agents, Proxies**

Even if your requests are respectful, websites can detect:

Too many hits from the same IP
Repetitive User-Agent strings
Headers that don’t match real browser behavior

To avoid this, we rotate
- User-Agents to simulate different browsers
- Headers to mimic real-world requests
- Proxies to distribute traffic across IPs

Real browsers always send User-Agent as part of the header. 

---

Web crawling is I/O-bound (waiting for network), not CPU-bound (heavy computation).

```python
from concurrent.futures import ThreadPoolExecutor

# Uses OS threads (not async!)
with ThreadPoolExecutor(max_workers=5) as executor:
    future = executor.submit(requests.get, url)  # Runs in separate thread
    result = future.result()  # Blocks until done
```

**ThreadPoolExecutor**
- Creates real OS threads
- Each thread runs synchronous code (like requests.get())
- OS scheduler decides when to switch between threads
- NOT async - just traditional threading


```python
from concurrent.futures import ProcessPoolExecutor

# Uses separate processes (for CPU-bound work)
with ProcessPoolExecutor(max_workers=5) as executor:
    future = executor.submit(heavy_computation, data)
    result = future.result()
```

**ProcessPoolExecutor**
- Creates separate Python processes
- Each process has its own Python interpreter and memory
- Bypasses GIL (each process has its own GIL)
- Good for CPU-bound work, bad for I/O (huge overhead)
- Uses multiprocessing under the hood

```python
import asyncio
import aiohttp

# Uses single thread + event loop
async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()

# Event loop manages switching between tasks
asyncio.run(fetch(url))
```

**Async / Await**
- Single thread with event loop
- Cooperative multitasking (await = "switch to another task")
- No OS thread switching
- Explicitly async code

Because python's request module is synchronous, I cannot use requests with async/await

## HTTP Libraries Comparison

**requests** (synchronous)
```python
import requests
response = requests.get(url)  # Blocks until response received
```
- Synchronous/blocking
- Use with ThreadPoolExecutor for concurrency
- Simple, widely used
- File: crawl.py

**httpx** (async support)
```python
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(url)  # Non-blocking with async
```
- Supports both sync and async
- Drop-in replacement for requests API
- Better for async/await patterns
- File: crawl_async.py

**aiohttp** (async only)
```python
import aiohttp
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        text = await response.text()
```
- Async only
- Very popular for async HTTP
- Different API from requests

---

Url structure
```
https://books.toscrape.com:8080/catalogue/page-2.html?sort=price#top
^^^^^  ^^^^^^^^^^^^^^^^^ ^^^^  ^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^ ^^^
scheme      netloc       port         path            query    fragment
```




