"""Authentication for Microsoft Graph API - delegates to shared auth."""

from __future__ import annotations

import sys
from pathlib import Path

# Make the shared package importable (lives at .github/skills/shared/)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared import auth as _shared  # noqa: E402

_GRAPH_SCOPE = "https://graph.microsoft.com/.default"


def get_token() -> str:
    """Return a valid OAuth access token for Microsoft Graph."""
    return _shared.get_token(_GRAPH_SCOPE, client_id=_shared.CLIENT_MICROSOFT_OFFICE)
