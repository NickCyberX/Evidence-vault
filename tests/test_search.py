# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for time-window search, keyword search, filters and clusters."""

import unittest

from core.errors import ValidationError
from core.models import Event
from core.search import events_in_window, find_first_at_or_after


def make_events():
    """Five sorted events, 10 seconds apart except one big gap."""
    return [
        Event("2026-11-03T09:00:00+00:00", "auth", "Failed login alice", "E-1"),
        Event("2026-11-03T09:00:10+00:00", "auth", "Failed login alice", "E-1"),
        Event("2026-11-03T09:00:20+00:00", "web", "GET admin page", ""),
        Event("2026-11-03T10:00:00+00:00", "web", "POST upload", "E-2"),
        Event("2026-11-03T10:00:05+00:00", "syslog", "Backup finished", ""),
    ]


class TestWindow(unittest.TestCase):
    """Binary search and window queries."""

    def test_find_first(self):
        events = make_events()
        self.assertEqual(find_first_at_or_after(events, "2026-11-03T09:00:10+00:00"), 1)
        self.assertEqual(find_first_at_or_after(events, "2026-11-03T09:00:11+00:00"), 2)

    def test_find_first_edges(self):
        events = make_events()
        self.assertEqual(find_first_at_or_after(events, "2000-01-01T00:00:00+00:00"), 0)
        self.assertEqual(find_first_at_or_after(events, "2999-01-01T00:00:00+00:00"), 5)
        self.assertEqual(find_first_at_or_after([], "2026-11-03T09:00:00+00:00"), 0)

    def test_window_includes_both_ends(self):
        found = events_in_window(
            make_events(), "2026-11-03T09:00:10Z", "2026-11-03T09:00:20Z"
        )
        self.assertEqual(len(found), 2)

    def test_window_before_and_after_everything(self):
        events = make_events()
        self.assertEqual(
            events_in_window(events, "2000-01-01T00:00:00Z", "2000-01-02T00:00:00Z"), []
        )
        self.assertEqual(
            events_in_window(events, "2999-01-01T00:00:00Z", "2999-01-02T00:00:00Z"), []
        )

    def test_window_start_after_end(self):
        with self.assertRaises(ValidationError):
            events_in_window(
                make_events(), "2026-11-04T00:00:00Z", "2026-11-03T00:00:00Z"
            )

    def test_window_bad_text(self):
        with self.assertRaises(ValidationError):
            events_in_window(make_events(), "nope", "2026-11-03T00:00:00Z")

    def test_window_on_empty_list(self):
        self.assertEqual(
            events_in_window([], "2026-11-03T00:00:00Z", "2026-11-04T00:00:00Z"), []
        )
