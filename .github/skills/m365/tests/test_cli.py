"""Tests for m365_cli.py CLI — argument parsing."""

from __future__ import annotations

import unittest

import m365_cli


class TestBuildParser(unittest.TestCase):
    """Verify that the parser accepts expected argument combinations."""

    def setUp(self):
        self.parser = m365_cli.build_parser()

    def test_sites_search(self):
        args = self.parser.parse_args(["sites", "search", "--keyword", "hr"])
        self.assertEqual(args.keyword, "hr")
        self.assertEqual(args.category, "sites")
        self.assertEqual(args.command, "search")

    def test_sites_get(self):
        args = self.parser.parse_args(["sites", "get", "--site-id", "abc"])
        self.assertEqual(args.site_id, "abc")

    def test_sites_get_by_path(self):
        args = self.parser.parse_args([
            "sites", "get-by-path",
            "--hostname", "contoso.sharepoint.com",
            "--site-path", "teams/hr",
        ])
        self.assertEqual(args.hostname, "contoso.sharepoint.com")
        self.assertEqual(args.site_path, "teams/hr")

    def test_sites_root(self):
        args = self.parser.parse_args(["sites", "root"])
        self.assertEqual(args.category, "sites")
        self.assertEqual(args.command, "root")

    def test_drives_list(self):
        args = self.parser.parse_args(["drives", "list", "--site-id", "s1"])
        self.assertEqual(args.site_id, "s1")

    def test_drives_download(self):
        args = self.parser.parse_args([
            "drives", "download",
            "--site-id", "s1",
            "--drive-id", "d1",
            "--item-id", "i1",
            "--output-path", "/tmp/file.pdf",
        ])
        self.assertEqual(args.output_path, "/tmp/file.pdf")

    def test_drives_items_by_path(self):
        args = self.parser.parse_args([
            "drives", "items-by-path",
            "--site-id", "s1",
            "--drive-id", "d1",
            "--path", "/Reports",
        ])
        self.assertEqual(args.path, "/Reports")

    def test_lists_items(self):
        args = self.parser.parse_args([
            "lists", "items",
            "--site-id", "s1",
            "--list-id", "l1",
            "--expand-fields", "true",
        ])
        self.assertEqual(args.expand_fields, "true")

    def test_search_files(self):
        args = self.parser.parse_args([
            "search", "files", "--query", "budget",
        ])
        self.assertEqual(args.query, "budget")

    def test_search_all(self):
        args = self.parser.parse_args([
            "search", "all",
            "--query", "report",
            "--entity-types", "driveItem,site",
        ])
        self.assertEqual(args.entity_types, "driveItem,site")

    def test_output_file_flag(self):
        args = self.parser.parse_args([
            "-o", "/tmp/out.json",
            "sites", "root",
        ])
        self.assertEqual(args.output_file, "/tmp/out.json")


if __name__ == "__main__":
    unittest.main()
