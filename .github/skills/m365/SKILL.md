---
name: m365
description: search, browse, and download documents from SharePoint (Microsoft 365)
---

# Microsoft 365 Skill

Search, browse, and download documents from SharePoint.
**All operations are read-only.**

## Setup

```bash
# Authentication: use Azure CLI
# IMPORTANT: Do NOT use --use-device-code (may be blocked by org policy).
# Use browser-based login from inside the container instead.
az config set core.login_experience_v2=off  # avoids interactive subscription picker that blocks automation
az login --allow-no-subscriptions -o tsv    # opens browser, no subscription required
```

## Usage

All commands below assume you are in the skill directory (the folder containing `m365_cli.py`).

```bash
python m365_cli.py [--output-file <path>] <category> <command> [--option value ...]
```

All commands output JSON to stdout by default. Use `--output-file <path>` (or `-o <path>`) to write the output directly to a file. **Prefer `--output-file` over shell redirection (`>`) to avoid unnecessary approval prompts.**

Use `--help` on any subcommand for usage details.

## Quick Reference

### sites — SharePoint sites

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `sites search` | `--keyword` | `--top` |
| `sites get` | `--site-id` | — |
| `sites get-by-path` | `--hostname --site-path` | — |
| `sites root` | — | — |
| `sites subsites` | `--site-id` | — |

**Site ID format:** `{hostname},{spsite-guid},{spweb-guid}` (e.g. `contoso.sharepoint.com,guid1,guid2`).
You can also look up a site by hostname and path using `sites get-by-path`.

### drives — Document libraries, folders, files

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `drives list` | `--site-id` | — |
| `drives get` | `--site-id --drive-id` | — |
| `drives default` | `--site-id` | — |
| `drives root-items` | `--site-id --drive-id` | `--top` |
| `drives children` | `--site-id --drive-id --item-id` | `--top` |
| `drives items-by-path` | `--site-id --drive-id --path` | `--top` |
| `drives get-item` | `--site-id --drive-id --item-id` | — |
| `drives get-item-by-path` | `--site-id --drive-id --path` | — |
| `drives download` | `--site-id --drive-id --item-id --output-path` | — |
| `drives download-by-path` | `--site-id --drive-id --path --output-path` | — |
| `drives download-by-url` | `--url --output-path` | — |

**Browsing files:** Use `drives root-items` to list items at the root level, `drives children` to navigate into folders by item ID, or `drives items-by-path` to navigate by path (e.g. `--path /Documents/Reports`).

**Downloading files:** Use `drives download` with an item ID, or `drives download-by-path` with a path. Both require `--output-path` for the local destination file. Use `drives download-by-url` to download directly from a SharePoint/OneDrive sharing URL — no site-id or drive-id needed.

### lists — SharePoint lists and list items

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `lists list` | `--site-id` | — |
| `lists get` | `--site-id --list-id` | — |
| `lists items` | `--site-id --list-id` | `--expand-fields`, `--top` |
| `lists get-item` | `--site-id --list-id --item-id` | `--expand-fields` |

**Boolean-style flags require an explicit value.** Use `--expand-fields true`, not just `--expand-fields`.

### search — Microsoft Search across SharePoint/OneDrive

| Command | Required Options | Optional |
|---------|-----------------|----------|
| `search files` | `--query` | `--top`, `--skip` |
| `search sites` | `--query` | `--top`, `--skip` |
| `search list-items` | `--query` | `--top`, `--skip` |
| `search all` | `--query` | `--entity-types`, `--top`, `--skip` |

**Search API notes:**
- `search files` searches for `driveItem` entities (files and folders in SharePoint/OneDrive).
- `search sites` searches for SharePoint `site` entities.
- `search list-items` searches for SharePoint `listItem` entities.
- `search all` searches across all types by default, or specify `--entity-types driveItem,site`.
- The Search API uses POST `/search/query` internally. Results include hit highlights.

## Scratch directory

The `_tmp/` folder inside the skill directory is checked in but its contents are git-ignored.
Use it for downloaded files and any other transient data:

```bash
# Examples
--output-file _tmp/sites.json
--output-path _tmp/document.docx
```

## Gotchas

- **No `--org` parameter.** Unlike the ADO skill, Microsoft Graph uses a global endpoint (`graph.microsoft.com`). The tenant is determined by your Azure CLI login.
- **Site IDs are compound.** A SharePoint site ID has the format `{hostname},{spsite-guid},{spweb-guid}`. Use `sites search` or `sites get-by-path` to discover site IDs.
- **Drive ID required for file operations.** Use `drives list` or `drives default` to get the drive ID for a site's document library.
- **Boolean-style flags require an explicit value.** Use `--expand-fields true`, not just `--expand-fields`.
- **Argument order matters.** `--output-file` is a top-level flag and must come **before** the category/command. Example: `python m365_cli.py --output-file out.json sites root`
- **Download commands write files directly.** `drives download` and `drives download-by-path` write binary files to `--output-path`, not to stdout.

## Common Workflows

### Find and download a document

```bash
# 1. Find the site
python m365_cli.py sites get-by-path --hostname contoso.sharepoint.com --site-path teams/engineering

# 2. List document libraries
python m365_cli.py drives list --site-id <site-id>

# 3. Browse folders
python m365_cli.py drives items-by-path --site-id <site-id> --drive-id <drive-id> --path /Shared Documents/Reports

# 4. Download a file
python m365_cli.py drives download-by-path --site-id <site-id> --drive-id <drive-id> --path /Shared Documents/Reports/Q4.docx --output-path _tmp/Q4.docx
```

### Download a file from a sharing URL

```bash
# Download directly from a SharePoint/OneDrive sharing URL (no site-id or drive-id needed)
python m365_cli.py drives download-by-url \
  --url "https://contoso.sharepoint.com/:w:/r/teams/engineering/Shared%20Documents/Report.docx?d=w1234&csf=1" \
  --output-path _tmp/Report.docx
```

### Convert downloaded Word files to Markdown

Word (`.docx`) files can be converted to Markdown using the `markitdown` CLI (installed via `requirements.txt`):

```bash
markitdown path-to-file.docx > document.md
```

### Search across all SharePoint

```bash
# Search for files containing "budget"
python m365_cli.py search files --query "budget 2025"

# Search for sites related to marketing
python m365_cli.py search sites --query "marketing"

# Search everything
python m365_cli.py search all --query "quarterly review" --top 10
```

## API Reference

This skill uses the [Microsoft Graph v1.0 REST API](https://learn.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0):

- **Sites**: [SharePoint sites API](https://learn.microsoft.com/en-us/graph/api/resources/sharepoint?view=graph-rest-1.0)
- **Drives**: [OneDrive/SharePoint files API](https://learn.microsoft.com/en-us/graph/api/resources/onedrive?view=graph-rest-1.0)
- **Lists**: [SharePoint lists API](https://learn.microsoft.com/en-us/graph/api/resources/list?view=graph-rest-1.0)
- **Search**: [Microsoft Search API](https://learn.microsoft.com/en-us/graph/search-concept-overview)
