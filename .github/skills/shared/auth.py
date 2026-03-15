"""
Shared authentication for MyClaw skills.

Uses InteractiveBrowserBrokerCredential (WAM broker) as the primary credential,
with AzureCliCredential and DefaultAzureCredential as fallbacks.

Provides **scope-aware** in-memory + disk caching so that tokens for different
audiences (e.g. MS Graph vs Azure DevOps) are stored side-by-side without
collisions.  Each scope gets its own entry in a single cache file keyed by the
scope string.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from azure.identity import DefaultAzureCredential, InteractiveBrowserCredential
from azure.identity.broker import InteractiveBrowserBrokerCredential

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Entra app registration (supports CAE / token protection via WAM broker)
_ENTRA_CLIENT_ID = os.environ.get(
    "MYCLAW_CLIENT_ID", "ba081686-5d24-4bc6-a0d6-d034ecffed87"
)
_ENTRA_TENANT_ID = os.environ.get(
    "MYCLAW_TENANT_ID", "72f988bf-86f1-41af-91ab-2d7cd011db47"
)

# Well-known first-party Microsoft client IDs
CLIENT_AZURE_CLI = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
CLIENT_MICROSOFT_OFFICE = "d3590ed6-52b3-4102-aeff-aad2292ab01c"

# Unified cache directory — one file holds all scopes.
_CACHE_DIR = Path(
    os.environ.get("MYCLAW_CACHE_DIR", Path.home() / ".cache" / "myclaw")
)
_CACHE_FILE = _CACHE_DIR / "token_cache.json"

# 5-minute buffer before real expiry.
_EXPIRY_BUFFER = 300

# In-memory cache: scope → {"token": str, "expires_on": float}
_token_cache: dict[str, dict] = {}


def _in_docker() -> bool:
    """Return True when running inside a Docker container."""
    return (
        os.path.exists("/.dockerenv")
        or os.environ.get("REMOTE_CONTAINERS") == "true"
    )

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _is_valid(entry: Optional[dict]) -> bool:
    """Return True if *entry* carries a token that hasn't (nearly) expired."""
    return entry is not None and entry.get("expires_on", 0) > time.time() + _EXPIRY_BUFFER


def _load_disk_cache() -> dict:
    """Read the whole disk cache (all scopes). Returns {} on any error."""
    try:
        if _CACHE_FILE.exists():
            return json.loads(_CACHE_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_disk_cache(cache: dict) -> None:
    """Persist the full scope-keyed cache dict to disk."""
    try:
        _CACHE_DIR.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(cache))
        _CACHE_FILE.chmod(0o600)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Window handle (needed by WAM broker)
# ---------------------------------------------------------------------------


def _get_window_handle() -> int:
    """Return a parent window handle suitable for the WAM broker."""
    if sys.platform == "win32":
        import win32gui  # pywin32

        return win32gui.GetForegroundWindow()
    # macOS / Linux fallback
    import msal

    return msal.PublicClientApplication.CONSOLE_WINDOW_HANDLE


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_token(
    scope: str,
    *,
    client_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> str:
    """Return a valid OAuth access token for *scope*.

    Parameters
    ----------
    scope : str
        The OAuth scope to request (e.g. ``https://graph.microsoft.com/.default``).
    client_id : str, optional
        Override the Entra app client ID.  Falls back to ``MYCLAW_CLIENT_ID``
        env-var, then to the built-in default.
    tenant_id : str, optional
        Override the Entra tenant ID.  Falls back to ``MYCLAW_TENANT_ID``
        env-var, then to the built-in default.

    Resolution order
    ~~~~~~~~~~~~~~~~
    1. In-memory cache  (scope-keyed)
    2. Disk cache        (scope-keyed)
    3. InteractiveBrowserCredential (Docker) / InteractiveBrowserBrokerCredential (WAM)
    4. DefaultAzureCredential       (CLI, managed identity, etc.)

    Because the cache is keyed by the full scope string, tokens for different
    audiences (MS Graph, Azure DevOps, …) coexist without collisions.
    """
    cid = _ENTRA_CLIENT_ID if client_id is None else client_id
    tid = _ENTRA_TENANT_ID if tenant_id is None else tenant_id

    # 1. In-memory cache
    entry = _token_cache.get(scope)
    if _is_valid(entry):
        return entry["token"]

    # 2. Disk cache
    disk_cache = _load_disk_cache()
    entry = disk_cache.get(scope)
    if _is_valid(entry):
        _token_cache[scope] = entry
        return entry["token"]

    # 3. Interactive credential (browser-based or broker-based)
    try:
        if _in_docker():
            interactive_kwargs: dict = {}
            if cid:
                interactive_kwargs["client_id"] = cid
            if tid:
                interactive_kwargs["tenant_id"] = tid
            cred = InteractiveBrowserCredential(**interactive_kwargs)
        else:
            broker_kwargs: dict = {
                "parent_window_handle": _get_window_handle(),
                "use_default_broker_account": True,
            }
            if cid:
                broker_kwargs["client_id"] = cid
            if tid:
                broker_kwargs["tenant_id"] = tid
            cred = InteractiveBrowserBrokerCredential(**broker_kwargs)
        access = cred.get_token(scope)
        token_data = {"token": access.token, "expires_on": access.expires_on}
        _token_cache[scope] = token_data
        disk_cache[scope] = token_data
        _save_disk_cache(disk_cache)
        return access.token
    except Exception:
        pass

    # 4. DefaultAzureCredential (CLI, managed identity, etc.)
    try:
        cred = DefaultAzureCredential()
        access = cred.get_token(scope)
        token_data = {"token": access.token, "expires_on": access.expires_on}
        _token_cache[scope] = token_data
        disk_cache = _load_disk_cache()
        disk_cache[scope] = token_data
        _save_disk_cache(disk_cache)
        return access.token
    except Exception:
        pass

    raise RuntimeError(
        f"Unable to authenticate for scope {scope!r}."
    )
