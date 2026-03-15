"""SharePoint list operations — lists and list items."""

from __future__ import annotations

from typing import Any, List, Optional

from . import client


def list_lists(site_id: str) -> List[Any]:
    """List all lists in a site.

    GET /sites/{site-id}/lists
    """
    return client.get_all(f"sites/{site_id}/lists")


def get_list(site_id: str, list_id: str) -> Any:
    """Get a specific list by ID.

    GET /sites/{site-id}/lists/{list-id}
    """
    return client.get(f"sites/{site_id}/lists/{list_id}")


def list_items(
    site_id: str,
    list_id: str,
    *,
    expand_fields: bool = False,
    top: Optional[int] = None,
) -> List[Any]:
    """List items in a SharePoint list.

    GET /sites/{site-id}/lists/{list-id}/items
    """
    params: dict[str, Any] = {}
    if expand_fields:
        params["expand"] = "fields"
    if top:
        params["$top"] = top
    return client.get_all(
        f"sites/{site_id}/lists/{list_id}/items",
        params=params,
    )


def get_item(
    site_id: str,
    list_id: str,
    item_id: str,
    *,
    expand_fields: bool = False,
) -> Any:
    """Get a specific list item.

    GET /sites/{site-id}/lists/{list-id}/items/{item-id}
    """
    params: dict[str, Any] = {}
    if expand_fields:
        params["expand"] = "fields"
    return client.get(
        f"sites/{site_id}/lists/{list_id}/items/{item_id}",
        params=params,
    )
