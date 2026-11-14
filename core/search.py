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
