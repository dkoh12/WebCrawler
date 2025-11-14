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