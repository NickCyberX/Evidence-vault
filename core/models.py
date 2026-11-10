# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review code in this file.
"""Data classes for the Evidence Vault (no user interface code here)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List

from core.errors import StorageError


@dataclass
class Case:
    """One investigation: its evidence, custody log and timeline."""

    case_id: str
    title: str
    investigator: str
    created_at: str
    evidence: Dict[str, EvidenceItem] = field(default_factory=dict)
    custody_log: List[CustodyEntry] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)


@dataclass
class EvidenceItem:
    """One piece of evidence and the SHA-256 fingerprint taken at intake."""

    evidence_id: str
    description: str
    source: str
    collector: str
    file_path: str
    sha256: str
    added_at: str


@dataclass
class CustodyEntry:
    """One line of the chain of custody, linked to the line before it."""

    entry_id: int
    evidence_id: str
    action: str
    actor: str
    timestamp: str
    previous_hash: str
    entry_hash: str


@dataclass
class Event:
    """One timeline event. The timestamp is always normalised UTC text."""

    timestamp: str
    source: str
    description: str
    evidence_id: str = ""
