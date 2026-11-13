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

    def test_altered_entry_is_found(self):
        self.add_three_entries()
        self.case.custody_log[1].actor = "Mallory"
        result = verify_chain(self.case)
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_index, 1)

    def test_removed_entry_is_found(self):
        self.add_three_entries()
        del self.case.custody_log[1]
        result = verify_chain(self.case)
        self.assertFalse(result.ok)
        self.assertEqual(result.broken_index, 1)

    def test_unmodified_file_passes(self):
        self.add_three_entries()
        self.assertEqual(verify_evidence_files(self.case), [])
        self.assertTrue(check_integrity(self.case)[0])

    def test_modified_file_is_found(self):
        self.add_three_entries()
        with open(self.path, "a", encoding="utf-8") as file:
            file.write(" tampered")
        problems = verify_evidence_files(self.case)
        self.assertEqual(len(problems), 1)
        self.assertIn("modified", problems[0])
        self.assertFalse(check_integrity(self.case)[0])

    def test_deleted_file_is_found(self):
        self.add_three_entries()
        os.remove(self.path)
        problems = verify_evidence_files(self.case)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing", problems[0])
