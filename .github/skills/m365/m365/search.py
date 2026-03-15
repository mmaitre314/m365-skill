"""Microsoft Search API — search for files, list items, and sites across SharePoint/OneDrive."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import client


def search_files(
    query: str,
    *,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search for files (driveItem) across SharePoint and OneDrive.

    POST /search/query
    entityTypes: ["driveItem"]
    """
    request: Dict[str, Any] = {
        "entityTypes": ["driveItem"],
        "query": {"queryString": query},
    }
    if top:
        request["from"] = skip or 0
        request["size"] = top
    elif skip:
        request["from"] = skip
    return client.post("search/query", json_body={"requests": [request]})


def search_sites(
    query: str,
    *,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search for SharePoint sites.

    POST /search/query
    entityTypes: ["site"]
    """
    request: Dict[str, Any] = {
        "entityTypes": ["site"],
        "query": {"queryString": query},
    }
    if top:
        request["from"] = skip or 0
        request["size"] = top
    elif skip:
        request["from"] = skip
    return client.post("search/query", json_body={"requests": [request]})


def search_list_items(
    query: str,
    *,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search for SharePoint list items.

    POST /search/query
    entityTypes: ["listItem"]
    """
    request: Dict[str, Any] = {
        "entityTypes": ["listItem"],
        "query": {"queryString": query},
    }
    if top:
        request["from"] = skip or 0
        request["size"] = top
    elif skip:
        request["from"] = skip
    return client.post("search/query", json_body={"requests": [request]})


def search_all(
    query: str,
    *,
    entity_types: Optional[List[str]] = None,
    top: Optional[int] = None,
    skip: Optional[int] = None,
) -> Any:
    """Search across multiple entity types (driveItem, listItem, site).

    POST /search/query
    Default entityTypes: ["driveItem", "listItem", "site"]
    """
    types = entity_types or ["driveItem", "listItem", "site"]
    request: Dict[str, Any] = {
        "entityTypes": types,
        "query": {"queryString": query},
    }
    if top:
        request["from"] = skip or 0
        request["size"] = top
    elif skip:
        request["from"] = skip
    return client.post("search/query", json_body={"requests": [request]})
