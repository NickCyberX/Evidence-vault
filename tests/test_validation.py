# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for input validation."""

import unittest

from core.errors import ValidationError
from core.validation import parse_timestamp, validate_evidence_id


class TestTimestamps(unittest.TestCase):
    """Normal, boundary and invalid timestamps."""

    def test_normal_utc(self):
        self.assertEqual(
            parse_timestamp("2026-11-03T14:30:00+00:00"), "2026-11-03T14:30:00+00:00"
        )

    def test_z_suffix(self):
        self.assertEqual(
            parse_timestamp("2026-11-03T14:30:00Z"), "2026-11-03T14:30:00+00:00"
        )

    def test_other_timezone_converted_to_utc(self):
        self.assertEqual(
            parse_timestamp("2026-11-03T15:30:00+01:00"), "2026-11-03T14:30:00+00:00"
        )

    def test_no_timezone_treated_as_utc(self):
        self.assertEqual(
            parse_timestamp("2026-11-03T14:30:00"), "2026-11-03T14:30:00+00:00"
        )

    def test_boundary_midnight(self):
        self.assertEqual(
            parse_timestamp("2026-11-03T00:00:00Z"), "2026-11-03T00:00:00+00:00"
        )

    def test_boundary_leap_day(self):
        self.assertEqual(
            parse_timestamp("2028-02-29T12:00:00Z"), "2028-02-29T12:00:00+00:00"
        )

    def test_invalid_leap_day(self):
        with self.assertRaises(ValidationError):
            parse_timestamp("2027-02-29T12:00:00Z")

    def test_invalid_values(self):
        for bad in ["", "   ", "not a date", "2026-13-01T00:00:00Z", None]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    parse_timestamp(bad)


class TestEvidenceIds(unittest.TestCase):
    """Evidence ID rules."""

    def test_valid_id_is_trimmed(self):
        self.assertEqual(validate_evidence_id("  E-001 ", set()), "E-001")

    def test_empty_id(self):
        with self.assertRaises(ValidationError):
            validate_evidence_id("   ", set())

    def test_too_long_id(self):
        with self.assertRaises(ValidationError):
            validate_evidence_id("A" * 31, set())

    def test_longest_allowed_id(self):
        self.assertEqual(validate_evidence_id("A" * 30, set()), "A" * 30)

    def test_bad_characters(self):
        with self.assertRaises(ValidationError):
            validate_evidence_id("E 001!", set())

    def test_duplicate_id(self):
        with self.assertRaises(ValidationError):
            validate_evidence_id("E-1", {"E-1"})
