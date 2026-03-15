"""Tests for m365/search.py — request body construction."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from m365 import search


class TestSearchFiles(unittest.TestCase):

    @patch("m365.search.client.post")
    def test_basic_search(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_files("quarterly report")
        body = mock_post.call_args[1]["json_body"]
        self.assertEqual(len(body["requests"]), 1)
        req = body["requests"][0]
        self.assertEqual(req["entityTypes"], ["driveItem"])
        self.assertEqual(req["query"]["queryString"], "quarterly report")

    @patch("m365.search.client.post")
    def test_with_pagination(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_files("report", top=10, skip=5)
        req = mock_post.call_args[1]["json_body"]["requests"][0]
        self.assertEqual(req["size"], 10)
        self.assertEqual(req["from"], 5)

    @patch("m365.search.client.post")
    def test_no_pagination_by_default(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_files("report")
        req = mock_post.call_args[1]["json_body"]["requests"][0]
        self.assertNotIn("size", req)
        self.assertNotIn("from", req)


class TestSearchSites(unittest.TestCase):

    @patch("m365.search.client.post")
    def test_entity_type_is_site(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_sites("marketing")
        req = mock_post.call_args[1]["json_body"]["requests"][0]
        self.assertEqual(req["entityTypes"], ["site"])
        self.assertEqual(req["query"]["queryString"], "marketing")


class TestSearchListItems(unittest.TestCase):

    @patch("m365.search.client.post")
    def test_entity_type_is_list_item(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_list_items("todo")
        req = mock_post.call_args[1]["json_body"]["requests"][0]
        self.assertEqual(req["entityTypes"], ["listItem"])


class TestSearchAll(unittest.TestCase):

    @patch("m365.search.client.post")
    def test_default_entity_types(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_all("budget")
        req = mock_post.call_args[1]["json_body"]["requests"][0]
        self.assertEqual(req["entityTypes"], ["driveItem", "listItem", "site"])

    @patch("m365.search.client.post")
    def test_custom_entity_types(self, mock_post):
        mock_post.return_value = {"value": []}
        search.search_all("budget", entity_types=["driveItem"])
        req = mock_post.call_args[1]["json_body"]["requests"][0]
        self.assertEqual(req["entityTypes"], ["driveItem"])


if __name__ == "__main__":
    unittest.main()
