# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for saving and loading cases."""

import os
import tempfile
import unittest

from core.errors import StorageError
from core.models import Case, CustodyEntry, Event, EvidenceItem
from core.storage import load_case, save_case


def make_case() -> Case:
    """Build a small case with one of everything."""
    case = Case("C-1", "Test case", "Alice", "2026-11-03T09:00:00+00:00")
    case.evidence["E-1"] = EvidenceItem(
        "E-1",
        "A file",
        "Laptop",
        "Alice",
        "file.txt",
        "abc123",
        "2026-11-03T09:05:00+00:00",
    )
    case.custody_log.append(
        CustodyEntry(
            1,
            "E-1",
            "REGISTERED",
            "Alice",
            "2026-11-03T09:05:00+00:00",
            "0" * 64,
            "def456",
        )
    )
    case.events.append(Event("2026-11-03T09:10:00+00:00", "auth", "Login", "E-1"))
    return case


class TestSaveLoad(unittest.TestCase):
    """Round-trip test."""

    def test_round_trip_keeps_everything(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "case.json")
            original = make_case()
            save_case(original, path)
            self.assertEqual(load_case(path), original)


class TestBadFiles(unittest.TestCase):
    """Loading files that are missing or broken."""

    def test_missing_file(self):
        with self.assertRaises(StorageError):
            load_case("this_file_does_not_exist.json")

    def test_corrupted_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "bad.json")
            with open(path, "w", encoding="utf-8") as file:
                file.write("{ this is not json")
            with self.assertRaises(StorageError):
                load_case(path)

    def test_json_with_missing_fields(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "wrong.json")
            with open(path, "w", encoding="utf-8") as file:
                file.write('{"title": "no id here"}')
            with self.assertRaises(StorageError):
                load_case(path)
