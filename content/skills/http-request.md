---
name: http-request
description: >
  Makes authenticated HTTP requests with retry logic, timeout handling, and
  structured error reporting. Foundation skill used by many other integrations.
version: 1.3.0
category: skills
tags: [http, api, networking, core]
author: platform-team
changelog: "v1.3: Configurable retry backoff"
---

# http-request

Base HTTP client skill with built-in resilience patterns.

## Features

- Exponential backoff retry (default: 3 attempts)
- Configurable timeouts (connect + read)
- Structured error responses
- Supports GET, POST, PUT, PATCH, DELETE

## Parameters

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `url` | string | — | Target URL |
| `method` | string | `GET` | HTTP method |
| `headers` | object | `{}` | Request headers |
| `body` | any | — | Request body (JSON-serialised) |
| `timeout` | int | `30` | Seconds before timeout |
| `retries` | int | `3` | Max retry attempts |

## Example

```python
result = http_request(
    url="https://api.example.com/data",
    method="POST",
    headers={"Authorization": "Bearer TOKEN"},
    body={"key": "value"},
    timeout=10,
)
```
