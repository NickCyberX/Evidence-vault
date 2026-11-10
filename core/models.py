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
