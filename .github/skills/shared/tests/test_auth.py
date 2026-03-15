"""Tests for shared/auth.py — scope-aware token caching and credential chain."""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from shared import auth


GRAPH_SCOPE = "https://graph.microsoft.com/.default"
ADO_SCOPE = "499b84ac-1321-427f-aa17-267ca6975798/.default"


class TestIsValid(unittest.TestCase):

    def test_none_is_invalid(self):
        self.assertFalse(auth._is_valid(None))

    def test_expired_is_invalid(self):
        self.assertFalse(auth._is_valid({"token": "t", "expires_on": time.time() - 100}))

    def test_within_buffer_is_invalid(self):
        # 4 minutes left, but 5-minute buffer → invalid
        self.assertFalse(auth._is_valid({"token": "t", "expires_on": time.time() + 240}))

    def test_valid_when_far_from_expiry(self):
        self.assertTrue(auth._is_valid({"token": "t", "expires_on": time.time() + 600}))


class TestDiskCache(unittest.TestCase):

    def test_returns_empty_dict_when_no_file(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(auth, "_CACHE_FILE", Path(d) / "missing.json"):
                self.assertEqual(auth._load_disk_cache(), {})

    def test_roundtrip_multiple_scopes(self):
        with tempfile.TemporaryDirectory() as d:
            cache_dir = Path(d)
            cache_file = cache_dir / "token_cache.json"
            with patch.object(auth, "_CACHE_DIR", cache_dir), \
                 patch.object(auth, "_CACHE_FILE", cache_file):
                data = {
                    GRAPH_SCOPE: {"token": "g-tok", "expires_on": time.time() + 3600},
                    ADO_SCOPE: {"token": "a-tok", "expires_on": time.time() + 3600},
                }
                auth._save_disk_cache(data)
                loaded = auth._load_disk_cache()
                self.assertEqual(loaded[GRAPH_SCOPE]["token"], "g-tok")
                self.assertEqual(loaded[ADO_SCOPE]["token"], "a-tok")

    def test_save_creates_directory_and_sets_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            cache_dir = Path(d) / "sub"
            cache_file = cache_dir / "token_cache.json"
            with patch.object(auth, "_CACHE_DIR", cache_dir), \
                 patch.object(auth, "_CACHE_FILE", cache_file):
                auth._save_disk_cache({"scope": {"token": "t", "expires_on": 9999999999}})
                self.assertTrue(cache_file.exists())
                if sys.platform != "win32":
                    mode = oct(cache_file.stat().st_mode & 0o777)
                    self.assertEqual(mode, "0o600")


class TestGetToken(unittest.TestCase):

    def setUp(self):
        auth._token_cache.clear()

    def tearDown(self):
        auth._token_cache.clear()

    def test_returns_from_memory_cache(self):
        auth._token_cache[GRAPH_SCOPE] = {"token": "mem-tok", "expires_on": time.time() + 600}
        self.assertEqual(auth.get_token(GRAPH_SCOPE), "mem-tok")

    def test_different_scopes_cached_separately(self):
        auth._token_cache[GRAPH_SCOPE] = {"token": "graph-tok", "expires_on": time.time() + 600}
        auth._token_cache[ADO_SCOPE] = {"token": "ado-tok", "expires_on": time.time() + 600}
        self.assertEqual(auth.get_token(GRAPH_SCOPE), "graph-tok")
        self.assertEqual(auth.get_token(ADO_SCOPE), "ado-tok")

    @patch.object(auth, "_load_disk_cache")
    def test_returns_from_disk_cache(self, mock_load):
        mock_load.return_value = {
            GRAPH_SCOPE: {"token": "disk-tok", "expires_on": time.time() + 600},
        }
        self.assertEqual(auth.get_token(GRAPH_SCOPE), "disk-tok")
        # Also promoted to in-memory cache
        self.assertEqual(auth._token_cache[GRAPH_SCOPE]["token"], "disk-tok")

    @patch.object(auth, "_save_disk_cache")
    @patch.object(auth, "_load_disk_cache", return_value={})
    @patch.object(auth, "_get_window_handle", return_value=0)
    @patch("shared.auth.InteractiveBrowserBrokerCredential")
    def test_broker_credential_used(self, mock_broker_cls, mock_handle, mock_load, mock_save):
        mock_access = MagicMock()
        mock_access.token = "broker-tok"
        mock_access.expires_on = time.time() + 3600
        mock_broker_cls.return_value.get_token.return_value = mock_access

        result = auth.get_token(GRAPH_SCOPE)

        self.assertEqual(result, "broker-tok")
        mock_broker_cls.return_value.get_token.assert_called_once_with(GRAPH_SCOPE)
        mock_save.assert_called_once()

    @patch.object(auth, "_save_disk_cache")
    @patch.object(auth, "_load_disk_cache", return_value={})
    @patch("shared.auth.InteractiveBrowserBrokerCredential", side_effect=Exception("no broker"))
    @patch("shared.auth.DefaultAzureCredential")
    def test_falls_back_to_default_credential(self, mock_default_cls, mock_broker, mock_load, mock_save):
        mock_access = MagicMock()
        mock_access.token = "default-tok"
        mock_access.expires_on = time.time() + 3600
        mock_default_cls.return_value.get_token.return_value = mock_access

        result = auth.get_token(ADO_SCOPE)

        self.assertEqual(result, "default-tok")
        mock_default_cls.return_value.get_token.assert_called_once_with(ADO_SCOPE)

    @patch.object(auth, "_save_disk_cache")
    @patch.object(auth, "_load_disk_cache", return_value={})
    @patch("shared.auth.InteractiveBrowserBrokerCredential", side_effect=Exception("no broker"))
    @patch("shared.auth.DefaultAzureCredential", side_effect=Exception("no default"))
    def test_raises_when_all_fail(self, mock_default, mock_broker, mock_load, mock_save):
        with self.assertRaises(RuntimeError) as ctx:
            auth.get_token(GRAPH_SCOPE)
        self.assertIn("Unable to authenticate", str(ctx.exception))
        self.assertIn(GRAPH_SCOPE, str(ctx.exception))

    def test_no_cross_scope_collision(self):
        """Expired Graph token must not be returned for ADO scope."""
        auth._token_cache[GRAPH_SCOPE] = {"token": "old-graph", "expires_on": time.time() - 100}
        auth._token_cache[ADO_SCOPE] = {"token": "valid-ado", "expires_on": time.time() + 600}

        # ADO should work fine
        self.assertEqual(auth.get_token(ADO_SCOPE), "valid-ado")

        # Graph should NOT return the expired token — would need to re-auth
        with patch.object(auth, "_load_disk_cache", return_value={}), \
             patch.object(auth, "_save_disk_cache"), \
             patch.object(auth, "_get_window_handle", return_value=0), \
             patch("shared.auth.InteractiveBrowserBrokerCredential") as mock_broker:
            mock_access = MagicMock()
            mock_access.token = "fresh-graph"
            mock_access.expires_on = time.time() + 3600
            mock_broker.return_value.get_token.return_value = mock_access

            result = auth.get_token(GRAPH_SCOPE)
            self.assertEqual(result, "fresh-graph")


if __name__ == "__main__":
    unittest.main()
