# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Tamper-evident chain of custody and integrity checks."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from core.case_manager import register_evidence
from core.errors import EvidenceError
from core.hashing import hash_file, hash_text
from core.models import Case, CustodyEntry, EvidenceItem
from core.validation import require_text, utc_now

GENESIS_HASH = "0" * 64


@dataclass
class ChainResult:
    """Result of walking the custody chain."""

    ok: bool
    broken_index: Optional[int]
    message: str


def compute_entry_hash(entry: CustodyEntry) -> str:
    """Hash every field of an entry (except its own hash) together."""
    text = "|".join(
        [
            str(entry.entry_id),
            entry.evidence_id,
            entry.action,
            entry.actor,
            entry.timestamp,
            entry.previous_hash,
        ]
    )
    return hash_text(text)
