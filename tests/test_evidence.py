# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for registering and managing evidence."""

import os
import tempfile
import unittest

from core.case_manager import (
    create_case,
    delete_evidence,
    edit_evidence_description,
    get_evidence,
    register_evidence,
)
from core.errors import EvidenceError, ValidationError


class TestEvidence(unittest.TestCase):
    """Evidence registration rules."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "note.txt")
        with open(self.path, "w", encoding="utf-8") as file:
            file.write("evidence")
        self.case = create_case("C-1", "Test", "Alice")

    def tearDown(self):
        self.folder.cleanup()

    def test_register_stores_hash(self):
        item = register_evidence(self.case, "E-1", "Note", "Laptop", "Alice", self.path)
        self.assertEqual(len(item.sha256), 64)
        self.assertIn("E-1", self.case.evidence)

    def test_duplicate_id_rejected(self):
        register_evidence(self.case, "E-1", "Note", "Laptop", "Alice", self.path)
        with self.assertRaises(ValidationError):
            register_evidence(self.case, "E-1", "Note", "Laptop", "Alice", self.path)

    def test_missing_file_rejected_and_nothing_stored(self):
        with self.assertRaises(EvidenceError):
            register_evidence(self.case, "E-1", "Note", "Laptop", "Alice", "nope.txt")
        self.assertEqual(self.case.evidence, {})

    def test_empty_description_rejected(self):
        with self.assertRaises(ValidationError):
            register_evidence(self.case, "E-1", "  ", "Laptop", "Alice", self.path)

    def test_get_edit_delete(self):
        register_evidence(self.case, "E-1", "Note", "Laptop", "Alice", self.path)
        edit_evidence_description(self.case, "E-1", "New text")
        self.assertEqual(get_evidence(self.case, "E-1").description, "New text")
        delete_evidence(self.case, "E-1")
        with self.assertRaises(EvidenceError):
            get_evidence(self.case, "E-1")
