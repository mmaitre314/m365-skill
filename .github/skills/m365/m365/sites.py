"""SharePoint site operations — sites, subsites."""

from __future__ import annotations

from typing import Any, List, Optional

from . import client


def search_sites(
    keyword: str,
    *,
    top: Optional[int] = None,
) -> Any:
    """Search for SharePoint sites by keyword.

    GET /sites?search={keyword}
    """
    params: dict[str, Any] = {"search": keyword}
    if top:
        params["$top"] = top
    return client.get("sites", params=params)


def get_site(site_id: str) -> Any:
    """Get a site by its ID.

    GET /sites/{site-id}
    """
    return client.get(f"sites/{site_id}")


def get_site_by_path(hostname: str, site_path: str) -> Any:
    """Get a site by hostname and server-relative path.

    GET /sites/{hostname}:/{site-path}
    Example: hostname=contoso.sharepoint.com, site_path=teams/hr
    """
    return client.get(f"sites/{hostname}:/{site_path}")


def get_root_site() -> Any:
    """Get the organization's root SharePoint site.

    GET /sites/root
    """
    return client.get("sites/root")


def list_subsites(site_id: str) -> List[Any]:
    """List sub-sites under a site.

    GET /sites/{site-id}/sites
    """
    return client.get_all(f"sites/{site_id}/sites")
