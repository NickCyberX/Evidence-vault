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


def require_text(text: str, label: str) -> str:
    """Return the text without spaces at the ends, or raise if it is empty."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValidationError(f"{label} cannot be empty.")
    return cleaned


def validate_evidence_id(text: str, existing_ids: Container[str]) -> str:
    """Check an evidence ID is well formed and not already used."""
    cleaned = require_text(text, "Evidence ID")
    if not ID_PATTERN.match(cleaned):
        raise ValidationError(
            "Evidence ID may only contain letters, digits and hyphens "
            "(maximum 30 characters)."
        )
    if cleaned in existing_ids:
        raise ValidationError(f"Evidence ID '{cleaned}' already exists.")
    return cleaned
