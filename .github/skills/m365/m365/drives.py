"""Drive (document library) operations — list drives, browse folders, get items."""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional

from . import client


def list_drives(site_id: str) -> List[Any]:
    """List all drives (document libraries) in a site.

    GET /sites/{site-id}/drives
    """
    return client.get_all(f"sites/{site_id}/drives")


def get_drive(site_id: str, drive_id: str) -> Any:
    """Get a specific drive by ID.

    GET /sites/{site-id}/drives/{drive-id}
    """
    return client.get(f"sites/{site_id}/drives/{drive_id}")


def get_default_drive(site_id: str) -> Any:
    """Get the default document library for a site.

    GET /sites/{site-id}/drive
    """
    return client.get(f"sites/{site_id}/drive")


def list_root_items(
    site_id: str,
    drive_id: str,
    *,
    top: Optional[int] = None,
) -> List[Any]:
    """List items in the root of a drive.

    GET /sites/{site-id}/drives/{drive-id}/root/children
    """
    params: dict[str, Any] = {}
    if top:
        params["$top"] = top
    return client.get_all(
        f"sites/{site_id}/drives/{drive_id}/root/children",
        params=params,
    )


def list_children(
    site_id: str,
    drive_id: str,
    item_id: str,
    *,
    top: Optional[int] = None,
) -> List[Any]:
    """List children of a folder item.

    GET /sites/{site-id}/drives/{drive-id}/items/{item-id}/children
    """
    params: dict[str, Any] = {}
    if top:
        params["$top"] = top
    return client.get_all(
        f"sites/{site_id}/drives/{drive_id}/items/{item_id}/children",
        params=params,
    )


def list_items_by_path(
    site_id: str,
    drive_id: str,
    folder_path: str,
    *,
    top: Optional[int] = None,
) -> List[Any]:
    """List items under a folder by path.

    GET /sites/{site-id}/drives/{drive-id}/root:/{path}:/children
    """
    # Strip leading slash for URL consistency
    folder_path = folder_path.lstrip("/")
    params: dict[str, Any] = {}
    if top:
        params["$top"] = top
    return client.get_all(
        f"sites/{site_id}/drives/{drive_id}/root:/{folder_path}:/children",
        params=params,
    )


def get_item(site_id: str, drive_id: str, item_id: str) -> Any:
    """Get metadata for a specific drive item.

    GET /sites/{site-id}/drives/{drive-id}/items/{item-id}
    """
    return client.get(f"sites/{site_id}/drives/{drive_id}/items/{item_id}")


def get_item_by_path(site_id: str, drive_id: str, item_path: str) -> Any:
    """Get metadata for a drive item by path.

    GET /sites/{site-id}/drives/{drive-id}/root:/{path}
    """
    item_path = item_path.lstrip("/")
    return client.get(f"sites/{site_id}/drives/{drive_id}/root:/{item_path}")


def download_item(site_id: str, drive_id: str, item_id: str, output_path: str) -> None:
    """Download a file by item ID and save to a local path.

    GET /sites/{site-id}/drives/{drive-id}/items/{item-id}/content
    The Graph API returns a 302 redirect to the actual download URL.
    requests follows redirects by default.
    """
    data = client.get_binary(f"sites/{site_id}/drives/{drive_id}/items/{item_id}/content")
    client.output_binary(data, output_path)


def download_item_by_path(site_id: str, drive_id: str, item_path: str, output_path: str) -> None:
    """Download a file by path and save to a local path.

    GET /sites/{site-id}/drives/{drive-id}/root:/{path}:/content
    """
    item_path = item_path.lstrip("/")
    data = client.get_binary(f"sites/{site_id}/drives/{drive_id}/root:/{item_path}:/content")
    client.output_binary(data, output_path)


# ---------------------------------------------------------------------------
# Sharing-URL helpers
# ---------------------------------------------------------------------------


def _encode_sharing_url(url: str) -> str:
    """Encode a sharing URL into a share token for the Graph /shares/ API.

    See https://learn.microsoft.com/en-us/graph/api/shares-get
    """
    encoded = base64.urlsafe_b64encode(url.encode("utf-8")).decode("ascii")
    return "u!" + encoded.rstrip("=")


def resolve_sharing_url(url: str) -> Dict[str, Any]:
    """Resolve a sharing URL to a driveItem metadata dict.

    GET /shares/{shareToken}/driveItem
    """
    token = _encode_sharing_url(url)
    return client.get(f"shares/{token}/driveItem")


def download_by_url(url: str, output_path: str) -> Dict[str, Any]:
    """Download a file directly from a SharePoint/OneDrive sharing URL.

    Uses the Graph /shares/ API to resolve and download in one step.
    Returns the driveItem metadata dict (name, size, etc.).
    """
    token = _encode_sharing_url(url)
    metadata = client.get(f"shares/{token}/driveItem")
    data = client.get_binary(f"shares/{token}/driveItem/content")
    client.output_binary(data, output_path)
    return metadata
