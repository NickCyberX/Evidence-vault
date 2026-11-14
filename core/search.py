# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Searching and grouping timeline events."""

import re
from datetime import datetime
from typing import Dict, List, Optional, Set

from core.errors import ValidationError
from core.models import Event
from core.validation import TIMESTAMP_FORMAT, parse_timestamp


def find_first_at_or_after(events: List[Event], timestamp: str) -> int:
    """Binary search: index of the first event at or after the timestamp.

    Returns len(events) if every event is earlier. Events must be sorted.
    """
    low, high = 0, len(events)
    while low < high:
        middle = (low + high) // 2
        if events[middle].timestamp < timestamp:
            low = middle + 1
        else:
            high = middle
    return low


def events_in_window(events: List[Event], start: str, end: str) -> List[Event]:
    """Return events from start to end, both included."""
    start_stamp = parse_timestamp(start)
    end_stamp = parse_timestamp(end)
    if start_stamp > end_stamp:
        raise ValidationError("The start time must not be after the end time.")
    index = find_first_at_or_after(events, start_stamp)
    found = []
    while index < len(events) and events[index].timestamp <= end_stamp:
        found.append(events[index])
        index += 1
    return found


def tokenize(text: str) -> List[str]:
    """Split text into lowercase words."""
    return re.findall(r"\w+", text.lower())


def build_index(events: List[Event]) -> Dict[str, Set[int]]:
    """Inverted index: word -> set of positions of events containing it."""
    index: Dict[str, Set[int]] = {}
    for position, event in enumerate(events):
        text = f"{event.description} {event.source} {event.evidence_id}"
        for word in tokenize(text):
            index.setdefault(word, set()).add(position)
    return index


def keyword_search(
    events: List[Event], index: Dict[str, Set[int]], text: str
) -> List[Event]:
    """Return events containing every word in the search text."""
    words = tokenize(text)
    if not words:
        raise ValidationError("Enter at least one search word.")
    matches = set(index.get(words[0], set()))
    for word in words[1:]:
        matches &= index.get(word, set())
    return [events[position] for position in sorted(matches)]


class TimelineSearcher:
    """Keeps an inverted index and rebuilds it only when the events change."""

    def __init__(self) -> None:
        self._events: Optional[List[Event]] = None
        self._count = -1
        self._index: Dict[str, Set[int]] = {}

    def search(self, events: List[Event], text: str) -> List[Event]:
        """Search the given events, rebuilding the index if needed."""
        if self._events is not events or self._count != len(events):
            self._index = build_index(events)
            self._events = events
            self._count = len(events)
        return keyword_search(events, self._index, text)


def filter_events(
    events: List[Event], source: Optional[str] = None, evidence_id: Optional[str] = None
) -> List[Event]:
    """Keep events matching the source and/or evidence ID (blank = ignore)."""
    source = (source or "").strip().lower()
    evidence_id = (evidence_id or "").strip().lower()
    return [
        event
        for event in events
        if (not source or event.source.lower() == source)
        and (not evidence_id or event.evidence_id.lower() == evidence_id)
    ]
