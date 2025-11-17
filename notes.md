
https://scrape.do/blog/web-crawler-python/

Today, pages are built with JavaScript frameworks that render content only in the browser. Many sites are hidden behind login walls, use dynamic URLs, or load content via background AJAX calls.

And to protect themselves from scraping and abuse, sites now use:

Bot detection systems like Cloudflare and DataDome
Behavior analysis and TLS fingerprint checks
CAPTCHA walls and aggressive IP blocking
Geo-restrictions and rate-limiting based on traffic patterns

All of this means that requests.get() by itself is rarely enough. Modern crawlers need more than basic HTTP calls.

They need to mimic real browsers, rotate identities, respect site policies, and recover from failures automatically.

---

Web crawling is I/O-bound (waiting for network), not CPU-bound (heavy computation).

```
from concurrent.futures import ThreadPoolExecutor

# Uses OS threads (not async!)
with ThreadPoolExecutor(max_workers=5) as executor:
    future = executor.submit(requests.get, url)  # Runs in separate thread
    result = future.result()  # Blocks until done
```

ThreadPoolExecutor
- Creates real OS threads
- Each thread runs synchronous code (like requests.get())
- OS scheduler decides when to switch between threads
- NOT async - just traditional threading


```
from concurrent.futures import ProcessPoolExecutor

# Uses separate processes (for CPU-bound work)
with ProcessPoolExecutor(max_workers=5) as executor:
    future = executor.submit(heavy_computation, data)
    result = future.result()
```

ProcessPoolExecutor
- Creates separate Python processes
- Each process has its own Python interpreter and memory
- Bypasses GIL (each process has its own GIL)
- Good for CPU-bound work, bad for I/O (huge overhead)
- Uses multiprocessing under the hood

```
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

Async / Await
- Single thread with event loop
- Cooperative multitasking (await = "switch to another task")
- No OS thread switching
- Explicitly async code

---

Url structure
```
https://books.toscrape.com:8080/catalogue/page-2.html?sort=price#top
^^^^^  ^^^^^^^^^^^^^^^^^ ^^^^  ^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^ ^^^
scheme      netloc       port         path            query    fragment
```




