# WebCrawler
a web crawler

## Setup

### Create Virtual Environment
```bash
python3 -m venv .venv
```

### Activate Virtual Environment
```bash
source .venv/bin/activate
```

### Deactivate Virtual Environment
```bash
deactivate
```

## HTTP Status Code Handling

| Code | Meaning | How to Handle |
|------|---------|---------------|
| 404 | Page not found | Skip, log, don't retry |
| 403/401 | Forbidden/Unauthorized | Rotate user-agent, proxy, or auth |
| 429 | Too Many Requests | Exponential backoff + jitter |
| 500/503 | Server error | Retry with backoff (up to 3x) |
| 301/302 | Redirect | Follow (but limit depth) |
| timeout | No response | Retry with longer timeout |

2xx - Success ✓

- 200: OK - everything worked
- 201: Created - new resource created
- 204: No Content - success but no data to return

3xx - Redirects →

- 301: Moved Permanently - URL changed forever
- 302: Found - temporary redirect
- 304: Not Modified - cached version is still good
→ Follow the redirect (requests does this automatically)

4xx (404, 403, 401) = you did something wrong
- 400: Bad Request - you sent malformed data
- 401: Unauthorized - you need to login
- 403: Forbidden - you're not allowed
- 404: Not Found - URL doesn't exist
- 429: Too Many Requests - you're going too fast

retrying won't help except for 429 with backoff.

5xx (500, 503) = server problem
- 500: Internal Server Error - server crashed/bug
- 502: Bad Gateway - proxy/load balancer issue
- 503: Service Unavailable - temporarily down
- 504: Gateway Timeout - upstream server didn't respond

1xx: Ignore, you won't encounter them
2xx: Success! Parse the data
3xx: Follow automatically (requests handles it)
4xx: Skip or fix your request
5xx: Retry with backoff

