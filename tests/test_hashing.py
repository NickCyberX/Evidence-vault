# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for file hashing."""

import hashlib
import os
import tempfile
import unittest

from core.errors import EvidenceError
from core.hashing import hash_file


class TestHashFile(unittest.TestCase):
    """SHA-256 of files."""

    def write(self, folder, text):
        path = os.path.join(folder, "f.txt")
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def test_known_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, "hello")
            self.assertEqual(hash_file(path), hashlib.sha256(b"hello").hexdigest())

    def test_one_character_changes_hash(self):
        with tempfile.TemporaryDirectory() as folder:
            first = hash_file(self.write(folder, "hello"))
            second = hash_file(self.write(folder, "hellp"))
            self.assertNotEqual(first, second)

    def test_empty_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.write(folder, "")
            self.assertEqual(hash_file(path), hashlib.sha256(b"").hexdigest())

