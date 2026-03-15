"""Tests for m365/auth.py - verifies the wrapper delegates to shared auth."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from m365 import auth


class TestGetToken(unittest.TestCase):

    @patch("m365.auth._shared")
    def test_delegates_to_shared_with_graph_scope(self, mock_shared):
        mock_shared.get_token.return_value = "graph-token"
        result = auth.get_token()
        self.assertEqual(result, "graph-token")
        mock_shared.get_token.assert_called_once_with(
            "https://graph.microsoft.com/.default",
            client_id=mock_shared.CLIENT_MICROSOFT_OFFICE,
        )


if __name__ == "__main__":
    unittest.main()
