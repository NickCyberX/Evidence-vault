# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for the report and CSV export."""

import csv
import os
import tempfile
import unittest

from core.case_manager import create_case
from core.chain import register_and_log
from core.models import Event
from core.report import export_timeline_csv, generate_text_report


class TestReport(unittest.TestCase):
    """Report content."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "note.txt")
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("evidence")
        self.case = create_case("C-1", "Test case", "Alice")
        register_and_log(self.case, "E-1", "Note", "Laptop", "Alice", self.path)
        self.case.events.append(
            Event("2026-11-03T09:00:00+00:00", "auth", "Login", "E-1")
        )

    def tearDown(self):
        self.folder.cleanup()

    def test_report_mentions_key_facts(self):
        text = generate_text_report(self.case)
        self.assertIn("C-1", text)
        self.assertIn("E-1", text)
        self.assertIn("Integrity: PASS", text)

    def test_report_shows_fail_when_tampered(self):
        with open(self.path, "a", encoding="utf-8") as file:
            file.write("x")
        self.assertIn("Integrity: FAIL", generate_text_report(self.case))

    def test_csv_export(self):
        out = os.path.join(self.folder.name, "out.csv")
        self.assertEqual(export_timeline_csv(self.case, out), 1)
        with open(out, newline="", encoding="utf-8") as file:
            rows = list(csv.reader(file))
        self.assertEqual(rows[0], ["timestamp", "source", "evidence_id", "description"])
        self.assertEqual(len(rows), 2)

    def test_csv_export_empty_timeline(self):
        self.case.events.clear()
        out = os.path.join(self.folder.name, "out.csv")
        self.assertEqual(export_timeline_csv(self.case, out), 0)
