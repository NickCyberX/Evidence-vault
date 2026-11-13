# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for the chain of custody and integrity checks."""

import os
import tempfile
import unittest

from core.case_manager import create_case
from core.chain import (
    append_entry,
    check_integrity,
    register_and_log,
    verify_chain,
    verify_evidence_files,
)
from core.errors import EvidenceError


class TestChain(unittest.TestCase):
    """Custody chain behaviour."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "note.txt")
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("evidence")
        self.case = create_case("C-1", "Test", "Alice")

    def tearDown(self):
        self.folder.cleanup()

    def add_three_entries(self):
        register_and_log(self.case, "E-1", "Note", "Laptop", "Alice", self.path)
        append_entry(self.case, "E-1", "TRANSFERRED", "Bob")
        append_entry(self.case, "", "CASE REVIEWED", "Carol")

    def test_empty_chain_is_valid(self):
        self.assertTrue(verify_chain(self.case).ok)

    def test_single_entry_chain_is_valid(self):
        register_and_log(self.case, "E-1", "Note", "Laptop", "Alice", self.path)
        self.assertEqual(len(self.case.custody_log), 1)
        self.assertTrue(verify_chain(self.case).ok)

    def test_three_entry_chain_is_valid(self):
        self.add_three_entries()
        self.assertTrue(verify_chain(self.case).ok)

    def test_unknown_evidence_rejected(self):
        with self.assertRaises(EvidenceError):
            append_entry(self.case, "E-99", "VIEWED", "Alice")
