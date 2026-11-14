# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for importing and merging events."""

import os
import tempfile
import unittest

from core.case_manager import create_case
from core.errors import StorageError, ValidationError
from core.models import Event
from core.timeline import (
    add_events,
    import_csv_events,
    import_events,
    import_text_log,
    merge_timelines,
    parse_log_line,
)


class TestImport(unittest.TestCase):
    """Importing files."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, text):
        path = os.path.join(self.folder.name, name)
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        return path

    def test_csv_import_sorts_and_normalises(self):
        path = self.write(
            "a.csv",
            "timestamp,description\n"
            "2026-11-03T10:00:00+01:00,second\n"
            "2026-11-03T08:00:00Z,first\n",
        )
        events, skipped = import_csv_events(path, "auth")
        self.assertEqual(skipped, 0)
        self.assertEqual([e.description for e in events], ["first", "second"])
        self.assertEqual(events[1].timestamp, "2026-11-03T09:00:00+00:00")

    def test_csv_bad_row_skipped(self):
        path = self.write(
            "a.csv", "timestamp,description\noops,bad\n2026-11-03T08:00:00Z,good\n"
        )
        events, skipped = import_csv_events(path, "auth")
        self.assertEqual((len(events), skipped), (1, 1))

    def test_empty_csv(self):
        path = self.write("a.csv", "timestamp,description\n")
        self.assertEqual(import_csv_events(path, "auth"), ([], 0))

    def test_text_log_skips_blank_and_bad_lines(self):
        path = self.write("a.txt", "2026-11-03T08:00:00Z host ok\n\nnonsense line\n")
        events, skipped = import_text_log(path, "syslog")
        self.assertEqual((len(events), skipped), (1, 1))

    def test_parse_log_line_needs_message(self):
        with self.assertRaises(ValidationError):
            parse_log_line("2026-11-03T08:00:00Z", "syslog")

    def test_missing_file(self):
        with self.assertRaises(StorageError):
            import_events("missing.csv", "auth")

    def test_sample_files_import(self):
        events, skipped = import_events(
            os.path.join("sample_data", "web_log.csv"), "web"
        )
        self.assertEqual((len(events), skipped), (3, 1))


class TestMerge(unittest.TestCase):
    """Merging timelines."""

    def ev(self, stamp, text="x"):
        return Event(stamp, "s", text)

    def test_interleaved_sources(self):
        first = [
            self.ev("2026-01-01T00:00:01+00:00"),
            self.ev("2026-01-01T00:00:05+00:00"),
        ]
        second = [self.ev("2026-01-01T00:00:03+00:00")]
        merged = merge_timelines([first, second])
        self.assertEqual(
            [e.timestamp[-14:-6] for e in merged], ["00:00:01", "00:00:03", "00:00:05"]
        )

    def test_empty_and_single_sources(self):
        one = [self.ev("2026-01-01T00:00:01+00:00")]
        self.assertEqual(merge_timelines([[], one]), one)
        self.assertEqual(merge_timelines([]), [])

    def test_identical_timestamps_kept(self):
        same = "2026-01-01T00:00:01+00:00"
        merged = merge_timelines([[self.ev(same, "a")], [self.ev(same, "b")]])
        self.assertEqual(len(merged), 2)

    def test_add_events_keeps_case_sorted(self):
        case = create_case("C-1", "T", "A")
        add_events(case, [self.ev("2026-01-01T00:00:09+00:00")])
        add_events(case, [self.ev("2026-01-01T00:00:02+00:00")])
        stamps = [e.timestamp for e in case.events]
        self.assertEqual(stamps, sorted(stamps))
