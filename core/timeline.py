# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Importing events from files and merging them into one timeline."""

import csv
import heapq
from typing import List, Tuple

from core.errors import StorageError, ValidationError
from core.models import Case, Event
from core.validation import parse_timestamp


def import_csv_events(
    path: str, source_name: str, evidence_id: str = ""
) -> Tuple[List[Event], int]:
    """Read a CSV with 'timestamp' and 'description' columns.

    Returns (events sorted by time, number of bad rows skipped).
    """
    events: List[Event] = []
    skipped = 0
    try:
        with open(path, newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                try:
                    stamp = parse_timestamp(row.get("timestamp") or "")
                    description = (row.get("description") or "").strip()
                    if not description:
                        raise ValidationError("Empty description.")
                    events.append(Event(stamp, source_name, description, evidence_id))
                except ValidationError:
                    skipped += 1
    except FileNotFoundError:
        raise StorageError(f"File not found: '{path}'") from None
    except (OSError, UnicodeDecodeError, csv.Error) as err:
        raise StorageError(f"Could not read '{path}': {err}") from err
    events.sort(key=lambda event: event.timestamp)
    return events, skipped
