#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This module tests the archive function.
"""

import os
import unittest
from unittest.mock import patch

from testfixtures import TempDirectory

from src.IntuneCD.intunecdlib.archive import Archive


class TestMoveToArchive(unittest.TestCase):
    """Test class for move_to_archive."""

    def setUp(self) -> None:
        self.directory = TempDirectory()
        self.directory.create()
        self.d = self.directory.makedir("fake_path")
        self.archive_folder = self.directory.path + "/__archive__"

        self.directory.write(
            "fake_path/test.json",
            '{"test": "test"}',
            encoding="utf-8",
        )

        self.directory.write(
            "Management Intents/test_intent.json",
            '{"test": "test"}',
            encoding="utf-8",
        )

        self.directory.write(
            "test.json",
            '{"test": "test"}',
            encoding="utf-8",
        )

        self.createdFile = ["test.json"]

        self.datetime = patch("src.IntuneCD.intunecdlib.archive.datetime")
        self.datetime = self.datetime.start()
        self.datetime.return_value = "2020-01-01_00-00-00"

    def tearDown(self):
        self.directory.cleanup()
        self.datetime.stop()

    def test_folder_exists(self):
        """The archive folder should be created."""

        Archive(path=self.directory.path, filetype="json").move_to_archive(
            self.createdFile
        )

        archive_path = os.path.join(self.directory.path, "__archive__")
        self.assertTrue(os.path.exists(archive_path))

    def test_file_moved(self):
        """The files should be moved to the archive folder."""

        self.createdFile = []

        archive = Archive(path=self.directory.path, filetype="json")
        archive.move_to_archive(self.createdFile)
        archive_path = os.path.join(
            self.directory.path, "__archive__", archive.date_tag
        )

        self.assertTrue(os.path.exists(os.path.join(archive_path, "test.json")))
        self.assertTrue(os.path.exists(os.path.join(archive_path, "test_intent.json")))


if __name__ == "__main__":
    unittest.main()
