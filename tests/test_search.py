# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tests for time-window search, keyword search, filters and clusters."""

import unittest

from core.errors import ValidationError
from core.models import Event
from core.search import (
    TimelineSearcher,
    build_index,
    cluster_events,
    events_in_window,
    filter_events,
    find_first_at_or_after,
    keyword_search,
)


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


class TestKeywordAndFilter(unittest.TestCase):
    """Index search and filters."""

    def test_single_word(self):
        events = make_events()
        found = keyword_search(events, build_index(events), "login")
        self.assertEqual(len(found), 2)

    def test_two_words_must_both_match(self):
        events = make_events()
        self.assertEqual(
            len(keyword_search(events, build_index(events), "failed alice")), 2
        )
        self.assertEqual(
            keyword_search(events, build_index(events), "failed upload"), []
        )

    def test_case_insensitive_and_no_match(self):
        events = make_events()
        self.assertEqual(len(keyword_search(events, build_index(events), "BACKUP")), 1)
        self.assertEqual(keyword_search(events, build_index(events), "zzz"), [])

    def test_empty_search_rejected(self):
        events = make_events()
        with self.assertRaises(ValidationError):
            keyword_search(events, build_index(events), "   ")

    def test_searcher_rebuilds_when_events_change(self):
        searcher = TimelineSearcher()
        events = make_events()
        self.assertEqual(len(searcher.search(events, "backup")), 1)
        more = events + [Event("2026-11-03T11:00:00+00:00", "x", "backup again", "")]
        self.assertEqual(len(searcher.search(more, "backup")), 2)

    def test_filter(self):
        events = make_events()
        self.assertEqual(len(filter_events(events, source="WEB")), 2)
        self.assertEqual(len(filter_events(events, evidence_id="e-1")), 2)
        self.assertEqual(len(filter_events(events, "web", "E-2")), 1)
        self.assertEqual(len(filter_events(events)), 5)


class TestClusters(unittest.TestCase):
    """Sliding-window grouping."""

    def test_two_bursts(self):
        clusters = cluster_events(make_events(), 30)
        self.assertEqual([len(c) for c in clusters], [3, 2])

    def test_gap_zero_separates_everything(self):
        self.assertEqual(len(cluster_events(make_events(), 0)), 5)

    def test_empty_and_single(self):
        self.assertEqual(cluster_events([], 30), [])
        self.assertEqual(len(cluster_events(make_events()[:1], 30)), 1)

    def test_negative_gap_rejected(self):
        with self.assertRaises(ValidationError):
            cluster_events(make_events(), -1)
