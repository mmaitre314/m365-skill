"""Tests for m365/sites.py — URL construction and parameters."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from m365 import sites


class TestSearchSites(unittest.TestCase):

    @patch("m365.sites.client.get")
    def test_keyword_param(self, mock_get):
        mock_get.return_value = {"value": []}
        sites.search_sites("engineering")
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "sites")
        self.assertEqual(kwargs["params"]["search"], "engineering")

    @patch("m365.sites.client.get")
    def test_with_top(self, mock_get):
        mock_get.return_value = {"value": []}
        sites.search_sites("eng", top=5)
        self.assertEqual(mock_get.call_args[1]["params"]["$top"], 5)


class TestGetSite(unittest.TestCase):

    @patch("m365.sites.client.get")
    def test_path(self, mock_get):
        mock_get.return_value = {"id": "abc"}
        sites.get_site("contoso.sharepoint.com,guid1,guid2")
        mock_get.assert_called_once_with("sites/contoso.sharepoint.com,guid1,guid2")


class TestGetSiteByPath(unittest.TestCase):

    @patch("m365.sites.client.get")
    def test_path_construction(self, mock_get):
        mock_get.return_value = {"id": "abc"}
        sites.get_site_by_path("contoso.sharepoint.com", "teams/hr")
        mock_get.assert_called_once_with("sites/contoso.sharepoint.com:/teams/hr")


class TestGetRootSite(unittest.TestCase):

    @patch("m365.sites.client.get")
    def test_calls_root(self, mock_get):
        mock_get.return_value = {"id": "root"}
        sites.get_root_site()
        mock_get.assert_called_once_with("sites/root")


class TestListSubsites(unittest.TestCase):

    @patch("m365.sites.client.get_all")
    def test_path(self, mock_get_all):
        mock_get_all.return_value = []
        sites.list_subsites("site-123")
        mock_get_all.assert_called_once_with("sites/site-123/sites")


if __name__ == "__main__":
    unittest.main()
