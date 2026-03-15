"""Tests for m365/drives.py — URL construction and parameters."""

from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch

from m365 import drives


class TestListDrives(unittest.TestCase):

    @patch("m365.drives.client.get_all")
    def test_path(self, mock_get_all):
        mock_get_all.return_value = []
        drives.list_drives("site-1")
        mock_get_all.assert_called_once_with("sites/site-1/drives")


class TestGetDefaultDrive(unittest.TestCase):

    @patch("m365.drives.client.get")
    def test_path(self, mock_get):
        mock_get.return_value = {"id": "drv"}
        drives.get_default_drive("site-1")
        mock_get.assert_called_once_with("sites/site-1/drive")


class TestListRootItems(unittest.TestCase):

    @patch("m365.drives.client.get_all")
    def test_path(self, mock_get_all):
        mock_get_all.return_value = []
        drives.list_root_items("site-1", "drv-1")
        args, kwargs = mock_get_all.call_args
        self.assertEqual(args[0], "sites/site-1/drives/drv-1/root/children")

    @patch("m365.drives.client.get_all")
    def test_with_top(self, mock_get_all):
        mock_get_all.return_value = []
        drives.list_root_items("site-1", "drv-1", top=10)
        kwargs = mock_get_all.call_args[1]
        self.assertEqual(kwargs["params"]["$top"], 10)


class TestListItemsByPath(unittest.TestCase):

    @patch("m365.drives.client.get_all")
    def test_path_construction(self, mock_get_all):
        mock_get_all.return_value = []
        drives.list_items_by_path("site-1", "drv-1", "/Documents/Reports")
        args, _ = mock_get_all.call_args
        self.assertEqual(args[0], "sites/site-1/drives/drv-1/root:/Documents/Reports:/children")

    @patch("m365.drives.client.get_all")
    def test_strips_leading_slash(self, mock_get_all):
        mock_get_all.return_value = []
        drives.list_items_by_path("site-1", "drv-1", "Docs")
        args, _ = mock_get_all.call_args
        self.assertEqual(args[0], "sites/site-1/drives/drv-1/root:/Docs:/children")


class TestGetItemByPath(unittest.TestCase):

    @patch("m365.drives.client.get")
    def test_path(self, mock_get):
        mock_get.return_value = {"id": "item-1"}
        drives.get_item_by_path("site-1", "drv-1", "/Reports/Q1.docx")
        mock_get.assert_called_once_with("sites/site-1/drives/drv-1/root:/Reports/Q1.docx")


class TestDownloadItem(unittest.TestCase):

    @patch("m365.drives.client.output_binary")
    @patch("m365.drives.client.get_binary")
    def test_download_path(self, mock_get_binary, mock_output):
        mock_get_binary.return_value = b"file-content"
        drives.download_item("site-1", "drv-1", "item-1", "/tmp/file.docx")
        mock_get_binary.assert_called_once_with(
            "sites/site-1/drives/drv-1/items/item-1/content",
        )
        mock_output.assert_called_once_with(b"file-content", "/tmp/file.docx")


class TestDownloadItemByPath(unittest.TestCase):

    @patch("m365.drives.client.output_binary")
    @patch("m365.drives.client.get_binary")
    def test_download_by_path(self, mock_get_binary, mock_output):
        mock_get_binary.return_value = b"content"
        drives.download_item_by_path("site-1", "drv-1", "/Reports/Q1.docx", "/tmp/Q1.docx")
        mock_get_binary.assert_called_once_with(
            "sites/site-1/drives/drv-1/root:/Reports/Q1.docx:/content",
        )


class TestEncodeSharingUrl(unittest.TestCase):

    def test_encoding(self):
        url = "https://contoso.sharepoint.com/:w:/r/sites/team/Doc.docx"
        token = drives._encode_sharing_url(url)
        self.assertTrue(token.startswith("u!"))
        # Must not contain padding '='
        self.assertNotIn("=", token)


class TestDownloadByUrl(unittest.TestCase):

    @patch("m365.drives.client.output_binary")
    @patch("m365.drives.client.get_binary")
    @patch("m365.drives.client.get")
    def test_download_by_url(self, mock_get, mock_get_binary, mock_output):
        mock_get.return_value = {"name": "Doc.docx", "size": 1024, "id": "item-1"}
        mock_get_binary.return_value = b"docx-bytes"
        url = "https://contoso.sharepoint.com/:w:/r/sites/team/Doc.docx"
        result = drives.download_by_url(url, "/tmp/Doc.docx")
        # Verify metadata call
        token = drives._encode_sharing_url(url)
        mock_get.assert_called_once_with(f"shares/{token}/driveItem")
        # Verify download call
        mock_get_binary.assert_called_once_with(f"shares/{token}/driveItem/content")
        # Verify output
        mock_output.assert_called_once_with(b"docx-bytes", "/tmp/Doc.docx")
        self.assertEqual(result["name"], "Doc.docx")


class TestResolveSharingUrl(unittest.TestCase):

    @patch("m365.drives.client.get")
    def test_resolve(self, mock_get):
        mock_get.return_value = {"name": "File.docx", "id": "item-1"}
        url = "https://contoso.sharepoint.com/:w:/r/sites/team/File.docx"
        result = drives.resolve_sharing_url(url)
        token = drives._encode_sharing_url(url)
        mock_get.assert_called_once_with(f"shares/{token}/driveItem")
        self.assertEqual(result["name"], "File.docx")


if __name__ == "__main__":
    unittest.main()
