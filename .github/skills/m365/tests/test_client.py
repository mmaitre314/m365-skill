"""Tests for m365/client.py — URL building, output, retry, pagination."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from m365 import client


class TestBuildUrl(unittest.TestCase):
    """_build_url constructs correct URLs."""

    def test_simple_path(self):
        url = client._build_url("sites/root")
        self.assertEqual(url, "https://graph.microsoft.com/v1.0/sites/root")

    def test_leading_slash_stripped(self):
        url = client._build_url("/sites/root")
        self.assertEqual(url, "https://graph.microsoft.com/v1.0/sites/root")

    def test_absolute_url_passthrough(self):
        full = "https://graph.microsoft.com/v1.0/sites/root?$top=10"
        self.assertEqual(client._build_url(full), full)


class TestOutput(unittest.TestCase):

    def setUp(self):
        client._output_file = None

    def test_stdout_json(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_out:
            client.output({"key": "value"})
            result = json.loads(mock_out.getvalue())
            self.assertEqual(result, {"key": "value"})

    def test_file_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.json")
            client._output_file = path
            client.output({"key": "value"})
            with open(path) as f:
                result = json.loads(f.read())
            self.assertEqual(result, {"key": "value"})

    def test_text_to_file(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "out.txt")
            client._output_file = path
            client.output_text("hello world")
            with open(path) as f:
                self.assertEqual(f.read(), "hello world")

    def test_binary_output(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "file.bin")
            client.output_binary(b"\x89PNG", path)
            with open(path, "rb") as f:
                self.assertEqual(f.read(), b"\x89PNG")


class TestRequestWithRetry(unittest.TestCase):

    @patch("m365.client.requests.get")
    @patch("m365.client.auth.get_token", return_value="tok")
    def test_success_no_retry(self, _tok, mock_get):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        mock_get.return_value = resp
        result = client._request_with_retry(
            "GET", "https://example.com", headers={"Authorization": "Bearer tok"},
        )
        self.assertEqual(result, resp)
        mock_get.assert_called_once()

    @patch("m365.client.time.sleep")
    @patch("m365.client.requests.get")
    @patch("m365.client.auth.get_token", return_value="tok")
    def test_retry_on_429(self, _tok, mock_get, mock_sleep):
        fail_resp = MagicMock()
        fail_resp.status_code = 429
        fail_resp.headers = {"Retry-After": "1"}
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.raise_for_status = MagicMock()
        mock_get.side_effect = [fail_resp, ok_resp]
        result = client._request_with_retry(
            "GET", "https://example.com", headers={"Authorization": "Bearer tok"},
        )
        self.assertEqual(result, ok_resp)
        mock_sleep.assert_called_once_with(1)  # Retry-After header

    @patch("m365.client.time.sleep")
    @patch("m365.client.requests.get")
    @patch("m365.client.auth.get_token", return_value="tok")
    def test_retry_on_503_exponential_backoff(self, _tok, mock_get, mock_sleep):
        fail_resp = MagicMock()
        fail_resp.status_code = 503
        fail_resp.headers = {}
        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.raise_for_status = MagicMock()
        mock_get.side_effect = [fail_resp, ok_resp]
        result = client._request_with_retry(
            "GET", "https://example.com", headers={"Authorization": "Bearer tok"},
        )
        self.assertEqual(result, ok_resp)
        mock_sleep.assert_called_once_with(2)  # _RETRY_BACKOFF * (2^0)


class TestGetAll(unittest.TestCase):

    @patch("m365.client._request_with_retry")
    @patch("m365.client.auth.get_token", return_value="tok")
    def test_single_page(self, _tok, mock_req):
        resp = MagicMock()
        resp.json.return_value = {"value": [{"id": "1"}, {"id": "2"}]}
        mock_req.return_value = resp
        items = client.get_all("sites/123/drives")
        self.assertEqual(len(items), 2)

    @patch("m365.client._request_with_retry")
    @patch("m365.client.auth.get_token", return_value="tok")
    def test_follows_next_link(self, _tok, mock_req):
        resp1 = MagicMock()
        resp1.json.return_value = {
            "value": [{"id": "1"}],
            "@odata.nextLink": "https://graph.microsoft.com/v1.0/sites/123/drives?$skip=1",
        }
        resp2 = MagicMock()
        resp2.json.return_value = {"value": [{"id": "2"}]}
        mock_req.side_effect = [resp1, resp2]
        items = client.get_all("sites/123/drives")
        self.assertEqual(len(items), 2)
        # Second call should use the absolute nextLink URL
        second_call_url = mock_req.call_args_list[1][1].get("url") or mock_req.call_args_list[1][0][1]
        self.assertIn("$skip=1", second_call_url)


if __name__ == "__main__":
    unittest.main()
