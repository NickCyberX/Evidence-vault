# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Input checks shared by the text and GUI versions."""

import re
from datetime import datetime, timezone
from typing import Container

from core.errors import ValidationError

TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S+00:00"
ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,30}$")


def utc_now() -> str:
    """Return the current time as normalised UTC text."""
    return datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)


def parse_timestamp(text: str) -> str:
    """Convert ISO 8601 text to normalised UTC text, or raise ValidationError.

    Text with no time zone is treated as UTC.
    """
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValidationError("Timestamp cannot be empty.")
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).strftime(TIMESTAMP_FORMAT)
    except (ValueError, OverflowError):
        raise ValidationError(
            f"Invalid timestamp '{text}'. Example: 2026-11-03T14:30:00+00:00"
        ) from None
