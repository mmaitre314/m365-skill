# Microsoft 365 Skill

Search, browse, and download documents from SharePoint. Designed as a [GitHub Copilot skill](https://code.visualstudio.com/docs/copilot/chat/chat-agent-mode#_custom-instructions) so an AI agent can interact with M365 programmatically.

## Quick start

- Create a Python Virtual Environment: `python -m venv .venv`
- Activate it
   - Windows CMD: `.venv\Scripts\activate.bat`
   - Windows PowerShell: `.venv\Scripts\Activate.ps1`
   - Linux/Max: `source .venv/bin/activate`
- Install Python packages: `pip install -r requirements.txt`

## Project layout

```
.github/skills/
├── m365/                   # Microsoft 365 (SharePoint) skill
│   ├── m365/               # Python package
│   │   ├── auth.py         # Graph API token (delegates to shared auth)
│   │   ├── client.py       # Low-level HTTP client, retry, pagination
│   │   ├── drives.py       # Document libraries, folders, file download
│   │   ├── lists.py        # SharePoint lists and list items
│   │   ├── search.py       # Microsoft Search (files, sites, list items)
│   │   └── sites.py        # SharePoint sites
│   ├── tests/              # Unit tests for the m365 skill
│   ├── m365_cli.py         # CLI entry point
│   ├── SKILL.md            # Full command reference (used by Copilot)
│   └── _tmp/               # Scratch directory for downloads (git-ignored)
└── shared/                 # Shared utilities across skills
    ├── auth.py             # Scope-aware token caching (WAM broker + fallbacks)
    └── tests/              # Unit tests for shared utilities
```

## Running tests

From the repository root, with the virtual environment activated:

```bash
python -m pytest .github/skills/ -v
```

## Further reading

See [SKILL.md](.github/skills/m365/SKILL.md) for the full command reference, examples, and gotchas.
