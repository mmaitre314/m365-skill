"""
Low-level HTTP client for Microsoft Graph REST API.

All read-only operations go through this module. Handles authentication,
base URL construction, pagination, and error reporting.
"""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Dict, List, Optional

import requests

from . import auth

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"
_DEFAULT_TIMEOUT = 60  # seconds
_MAX_RETRIES = 2
_RETRY_BACKOFF = 2  # seconds, doubles each retry


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _headers() -> Dict[str, str]:
    token = auth.get_token()
    return {"Authorization": f"Bearer {token}", "Accept": "application/json"}


def _build_url(path: str) -> str:
    """Build full Graph API URL from a relative path."""
    if path.startswith("https://"):
        return path
    return f"{_GRAPH_BASE}/{path.lstrip('/')}"


# ---------------------------------------------------------------------------
# Public request helpers
# ---------------------------------------------------------------------------


def _request_with_retry(
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout: int = _DEFAULT_TIMEOUT,
) -> requests.Response:
    """Issue an HTTP request with automatic retry on transient failures."""
    last_exc: Optional[Exception] = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers, params=params, timeout=timeout)
            else:
                resp = requests.post(url, headers=headers, params=params, json=json_body, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504) and attempt < _MAX_RETRIES:
                # Respect Retry-After header if present
                retry_after = resp.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = int(retry_after)
                else:
                    wait = _RETRY_BACKOFF * (2 ** attempt)
                print(f"[retry] HTTP {resp.status_code} on {method} {url}, waiting {wait}s (attempt {attempt + 1}/{_MAX_RETRIES + 1})", file=sys.stderr)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                wait = _RETRY_BACKOFF * (2 ** attempt)
                print(f"[retry] {type(exc).__name__} on {method} {url}, waiting {wait}s (attempt {attempt + 1}/{_MAX_RETRIES + 1})", file=sys.stderr)
                time.sleep(wait)
            else:
                raise
    raise last_exc  # should not reach here, but satisfy type checker


def get(
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """Issue an authenticated GET and return the JSON body."""
    url = _build_url(path)
    resp = _request_with_retry("GET", url, headers=_headers(), params=params, timeout=_DEFAULT_TIMEOUT)
    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return resp.json()
    return resp.text


def get_binary(
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
) -> bytes:
    """Issue an authenticated GET and return the raw bytes (for file downloads)."""
    url = _build_url(path)
    hdrs = _headers()
    resp = _request_with_retry("GET", url, headers=hdrs, params=params, timeout=_DEFAULT_TIMEOUT)
    return resp.content


def post(
    path: str,
    *,
    json_body: Optional[Any] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Any:
    """Issue an authenticated POST (used for search endpoints)."""
    url = _build_url(path)
    hdrs = _headers()
    hdrs["Content-Type"] = "application/json"
    resp = _request_with_retry("POST", url, headers=hdrs, params=params, json_body=json_body, timeout=_DEFAULT_TIMEOUT)
    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        return resp.json()
    return resp.text


def get_all(
    path: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    max_pages: int = 20,
) -> List[Any]:
    """GET with @odata.nextLink pagination. Returns all items."""
    all_items: List[Any] = []
    url = _build_url(path)
    p = dict(params or {})
    for _ in range(max_pages):
        resp = _request_with_retry("GET", url, headers=_headers(), params=p, timeout=_DEFAULT_TIMEOUT)
        data = resp.json()
        all_items.extend(data.get("value", []))
        next_link = data.get("@odata.nextLink")
        if not next_link:
            break
        # nextLink is an absolute URL — use it directly, clear params
        url = next_link
        p = {}
    return all_items


# ---------------------------------------------------------------------------
# Output helper – used by CLI
# ---------------------------------------------------------------------------


_output_file: str | None = None


def set_output_file(path: str | None) -> None:
    """Set an optional file path for output (instead of stdout)."""
    global _output_file
    _output_file = path


def output(data: Any) -> None:
    """Pretty-print JSON to stdout or to the configured output file."""
    if _output_file:
        import pathlib
        pathlib.Path(_output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(_output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
            f.write("\n")
        print(f"Output written to {_output_file}")
    else:
        json.dump(data, sys.stdout, indent=2, default=str)
        print()


def output_text(text: str) -> None:
    """Write raw text to stdout or to the configured output file."""
    if _output_file:
        import pathlib
        pathlib.Path(_output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(_output_file, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Output written to {_output_file}")
    else:
        print(text)


def output_binary(data: bytes, path: str) -> None:
    """Write binary data to a file (for file downloads)."""
    import pathlib
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    print(f"Downloaded to {path}")
