#!/usr/bin/env python3
"""
Microsoft 365 read-only SharePoint query CLI.

Usage:  python m365_cli.py <category> <command> [options]

Searches, browses, and downloads documents from SharePoint via the
Microsoft Graph REST API. All operations are read-only.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from m365 import client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _int_or_none(v: str | None) -> int | None:
    return int(v) if v is not None else None


def _bool_flag(v: str | None) -> bool | None:
    if v is None:
        return None
    return v.lower() in ("true", "1", "yes")


def _output(data: Any) -> None:
    client.output(data)


# ===================================================================
# SITES
# ===================================================================

def cmd_sites_search(args: argparse.Namespace) -> None:
    from m365.sites import search_sites
    _output(search_sites(args.keyword, top=_int_or_none(args.top)))


def cmd_sites_get(args: argparse.Namespace) -> None:
    from m365.sites import get_site
    _output(get_site(args.site_id))


def cmd_sites_get_by_path(args: argparse.Namespace) -> None:
    from m365.sites import get_site_by_path
    _output(get_site_by_path(args.hostname, args.site_path))


def cmd_sites_root(args: argparse.Namespace) -> None:
    from m365.sites import get_root_site
    _output(get_root_site())


def cmd_sites_subsites(args: argparse.Namespace) -> None:
    from m365.sites import list_subsites
    _output(list_subsites(args.site_id))


# ===================================================================
# DRIVES
# ===================================================================

def cmd_drives_list(args: argparse.Namespace) -> None:
    from m365.drives import list_drives
    _output(list_drives(args.site_id))


def cmd_drives_get(args: argparse.Namespace) -> None:
    from m365.drives import get_drive
    _output(get_drive(args.site_id, args.drive_id))


def cmd_drives_default(args: argparse.Namespace) -> None:
    from m365.drives import get_default_drive
    _output(get_default_drive(args.site_id))


def cmd_drives_root_items(args: argparse.Namespace) -> None:
    from m365.drives import list_root_items
    _output(list_root_items(args.site_id, args.drive_id, top=_int_or_none(args.top)))


def cmd_drives_children(args: argparse.Namespace) -> None:
    from m365.drives import list_children
    _output(list_children(args.site_id, args.drive_id, args.item_id, top=_int_or_none(args.top)))


def cmd_drives_items_by_path(args: argparse.Namespace) -> None:
    from m365.drives import list_items_by_path
    _output(list_items_by_path(args.site_id, args.drive_id, args.path, top=_int_or_none(args.top)))


def cmd_drives_get_item(args: argparse.Namespace) -> None:
    from m365.drives import get_item
    _output(get_item(args.site_id, args.drive_id, args.item_id))


def cmd_drives_get_item_by_path(args: argparse.Namespace) -> None:
    from m365.drives import get_item_by_path
    _output(get_item_by_path(args.site_id, args.drive_id, args.path))


def cmd_drives_download(args: argparse.Namespace) -> None:
    from m365.drives import download_item
    download_item(args.site_id, args.drive_id, args.item_id, args.output_path)


def cmd_drives_download_by_path(args: argparse.Namespace) -> None:
    from m365.drives import download_item_by_path
    download_item_by_path(args.site_id, args.drive_id, args.path, args.output_path)


def cmd_drives_download_by_url(args: argparse.Namespace) -> None:
    from m365.drives import download_by_url
    metadata = download_by_url(args.url, args.output_path)
    _output({"name": metadata.get("name"), "size": metadata.get("size"), "id": metadata.get("id")})


# ===================================================================
# LISTS
# ===================================================================

def cmd_lists_list(args: argparse.Namespace) -> None:
    from m365.lists import list_lists
    _output(list_lists(args.site_id))


def cmd_lists_get(args: argparse.Namespace) -> None:
    from m365.lists import get_list
    _output(get_list(args.site_id, args.list_id))


def cmd_lists_items(args: argparse.Namespace) -> None:
    from m365.lists import list_items
    _output(list_items(
        args.site_id, args.list_id,
        expand_fields=_bool_flag(args.expand_fields) or False,
        top=_int_or_none(args.top),
    ))


def cmd_lists_get_item(args: argparse.Namespace) -> None:
    from m365.lists import get_item
    _output(get_item(
        args.site_id, args.list_id, args.item_id,
        expand_fields=_bool_flag(args.expand_fields) or False,
    ))


# ===================================================================
# SEARCH
# ===================================================================

def cmd_search_files(args: argparse.Namespace) -> None:
    from m365.search import search_files
    _output(search_files(args.query, top=_int_or_none(args.top), skip=_int_or_none(args.skip)))


def cmd_search_sites(args: argparse.Namespace) -> None:
    from m365.search import search_sites
    _output(search_sites(args.query, top=_int_or_none(args.top), skip=_int_or_none(args.skip)))


def cmd_search_list_items(args: argparse.Namespace) -> None:
    from m365.search import search_list_items
    _output(search_list_items(args.query, top=_int_or_none(args.top), skip=_int_or_none(args.skip)))


def cmd_search_all(args: argparse.Namespace) -> None:
    from m365.search import search_all
    types = args.entity_types.split(",") if args.entity_types else None
    _output(search_all(args.query, entity_types=types, top=_int_or_none(args.top), skip=_int_or_none(args.skip)))


# ===================================================================
# Parser
# ===================================================================

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="m365",
        description="Microsoft 365 read-only SharePoint query CLI (via Microsoft Graph).",
    )
    p.add_argument("-o", "--output-file", default=None, help="Write output to file instead of stdout")

    sub = p.add_subparsers(dest="category", required=True)

    # ---- sites ----
    sites = sub.add_parser("sites", help="SharePoint sites")
    sites_sub = sites.add_subparsers(dest="command", required=True)

    ss = sites_sub.add_parser("search", help="Search for sites by keyword")
    ss.add_argument("--keyword", required=True); ss.add_argument("--top")
    ss.set_defaults(func=cmd_sites_search)

    sg = sites_sub.add_parser("get", help="Get site by ID")
    sg.add_argument("--site-id", required=True)
    sg.set_defaults(func=cmd_sites_get)

    sgp = sites_sub.add_parser("get-by-path", help="Get site by hostname and path")
    sgp.add_argument("--hostname", required=True); sgp.add_argument("--site-path", required=True)
    sgp.set_defaults(func=cmd_sites_get_by_path)

    sr = sites_sub.add_parser("root", help="Get organization root site")
    sr.set_defaults(func=cmd_sites_root)

    sss = sites_sub.add_parser("subsites", help="List sub-sites")
    sss.add_argument("--site-id", required=True)
    sss.set_defaults(func=cmd_sites_subsites)

    # ---- drives ----
    drives = sub.add_parser("drives", help="Document libraries (drives), folders, files")
    drives_sub = drives.add_subparsers(dest="command", required=True)

    dl = drives_sub.add_parser("list", help="List drives in a site")
    dl.add_argument("--site-id", required=True)
    dl.set_defaults(func=cmd_drives_list)

    dg = drives_sub.add_parser("get", help="Get drive by ID")
    dg.add_argument("--site-id", required=True); dg.add_argument("--drive-id", required=True)
    dg.set_defaults(func=cmd_drives_get)

    dd = drives_sub.add_parser("default", help="Get default document library for a site")
    dd.add_argument("--site-id", required=True)
    dd.set_defaults(func=cmd_drives_default)

    dri = drives_sub.add_parser("root-items", help="List items at root of a drive")
    dri.add_argument("--site-id", required=True); dri.add_argument("--drive-id", required=True); dri.add_argument("--top")
    dri.set_defaults(func=cmd_drives_root_items)

    dc = drives_sub.add_parser("children", help="List children of a folder (by item ID)")
    dc.add_argument("--site-id", required=True); dc.add_argument("--drive-id", required=True)
    dc.add_argument("--item-id", required=True); dc.add_argument("--top")
    dc.set_defaults(func=cmd_drives_children)

    dip = drives_sub.add_parser("items-by-path", help="List items under a folder (by path)")
    dip.add_argument("--site-id", required=True); dip.add_argument("--drive-id", required=True)
    dip.add_argument("--path", required=True); dip.add_argument("--top")
    dip.set_defaults(func=cmd_drives_items_by_path)

    dgi = drives_sub.add_parser("get-item", help="Get item metadata by ID")
    dgi.add_argument("--site-id", required=True); dgi.add_argument("--drive-id", required=True)
    dgi.add_argument("--item-id", required=True)
    dgi.set_defaults(func=cmd_drives_get_item)

    dgip = drives_sub.add_parser("get-item-by-path", help="Get item metadata by path")
    dgip.add_argument("--site-id", required=True); dgip.add_argument("--drive-id", required=True)
    dgip.add_argument("--path", required=True)
    dgip.set_defaults(func=cmd_drives_get_item_by_path)

    ddl = drives_sub.add_parser("download", help="Download file by item ID")
    ddl.add_argument("--site-id", required=True); ddl.add_argument("--drive-id", required=True)
    ddl.add_argument("--item-id", required=True); ddl.add_argument("--output-path", required=True)
    ddl.set_defaults(func=cmd_drives_download)

    ddlp = drives_sub.add_parser("download-by-path", help="Download file by path")
    ddlp.add_argument("--site-id", required=True); ddlp.add_argument("--drive-id", required=True)
    ddlp.add_argument("--path", required=True); ddlp.add_argument("--output-path", required=True)
    ddlp.set_defaults(func=cmd_drives_download_by_path)

    ddlu = drives_sub.add_parser("download-by-url", help="Download file from a SharePoint/OneDrive sharing URL")
    ddlu.add_argument("--url", required=True, help="SharePoint or OneDrive sharing URL")
    ddlu.add_argument("--output-path", required=True, help="Local path to save the file")
    ddlu.set_defaults(func=cmd_drives_download_by_url)

    # ---- lists ----
    lists = sub.add_parser("lists", help="SharePoint lists and list items")
    lists_sub = lists.add_subparsers(dest="command", required=True)

    ll = lists_sub.add_parser("list", help="List all lists in a site")
    ll.add_argument("--site-id", required=True)
    ll.set_defaults(func=cmd_lists_list)

    lg = lists_sub.add_parser("get", help="Get list by ID")
    lg.add_argument("--site-id", required=True); lg.add_argument("--list-id", required=True)
    lg.set_defaults(func=cmd_lists_get)

    lit = lists_sub.add_parser("items", help="List items in a list")
    lit.add_argument("--site-id", required=True); lit.add_argument("--list-id", required=True)
    lit.add_argument("--expand-fields"); lit.add_argument("--top")
    lit.set_defaults(func=cmd_lists_items)

    lig = lists_sub.add_parser("get-item", help="Get specific list item")
    lig.add_argument("--site-id", required=True); lig.add_argument("--list-id", required=True)
    lig.add_argument("--item-id", required=True); lig.add_argument("--expand-fields")
    lig.set_defaults(func=cmd_lists_get_item)

    # ---- search ----
    srch = sub.add_parser("search", help="Microsoft Search across SharePoint/OneDrive")
    srch_sub = srch.add_subparsers(dest="command", required=True)

    sf = srch_sub.add_parser("files", help="Search for files (driveItem)")
    sf.add_argument("--query", required=True); sf.add_argument("--top"); sf.add_argument("--skip")
    sf.set_defaults(func=cmd_search_files)

    sst = srch_sub.add_parser("sites", help="Search for SharePoint sites")
    sst.add_argument("--query", required=True); sst.add_argument("--top"); sst.add_argument("--skip")
    sst.set_defaults(func=cmd_search_sites)

    sli = srch_sub.add_parser("list-items", help="Search for list items")
    sli.add_argument("--query", required=True); sli.add_argument("--top"); sli.add_argument("--skip")
    sli.set_defaults(func=cmd_search_list_items)

    sal = srch_sub.add_parser("all", help="Search across all entity types")
    sal.add_argument("--query", required=True); sal.add_argument("--entity-types", help="Comma-separated: driveItem,listItem,site")
    sal.add_argument("--top"); sal.add_argument("--skip")
    sal.set_defaults(func=cmd_search_all)

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    client.set_output_file(args.output_file)
    try:
        args.func(args)
    except Exception as exc:
        error_detail = json.dumps({"error": str(exc)})
        print(error_detail, file=sys.stderr)
        out_path = getattr(args, "output_file", None)
        if out_path:
            print(f"ERROR: failed to write {out_path} — {exc}")
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()
