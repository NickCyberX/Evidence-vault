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


def append_entry(case: Case, evidence_id: str, action: str, actor: str) -> CustodyEntry:
    """Add a new custody entry linked to the previous one."""
    evidence_id = (evidence_id or "").strip()
    if evidence_id and evidence_id not in case.evidence:
        raise EvidenceError(f"No evidence with ID '{evidence_id}'.")
    previous = case.custody_log[-1].entry_hash if case.custody_log else GENESIS_HASH
    entry = CustodyEntry(
        entry_id=len(case.custody_log) + 1,
        evidence_id=evidence_id,
        action=require_text(action, "Action"),
        actor=require_text(actor, "Actor"),
        timestamp=utc_now(),
        previous_hash=previous,
        entry_hash="",
    )
    entry.entry_hash = compute_entry_hash(entry)
    case.custody_log.append(entry)
    return entry


def register_and_log(
    case: Case,
    evidence_id: str,
    description: str,
    source: str,
    collector: str,
    file_path: str,
) -> EvidenceItem:
    """Register evidence and record a REGISTERED custody entry for it."""
    item = register_evidence(
        case, evidence_id, description, source, collector, file_path
    )
    append_entry(case, item.evidence_id, "REGISTERED", item.collector)
    return item


def verify_chain(case: Case) -> ChainResult:
    """Walk the chain and report the first entry that does not check out."""
    previous = GENESIS_HASH
    for index, entry in enumerate(case.custody_log):
        if entry.previous_hash != previous:
            return ChainResult(
                False,
                index,
                f"Entry {entry.entry_id} does not link to the one before it.",
            )
        if compute_entry_hash(entry) != entry.entry_hash:
            return ChainResult(
                False, index, f"Entry {entry.entry_id} has been altered."
            )
        previous = entry.entry_hash
    return ChainResult(
        True, None, f"Custody chain intact ({len(case.custody_log)} entries)."
    )


def verify_evidence_files(case: Case) -> List[str]:
    """Re-hash every evidence file and list the ones that no longer match."""
    problems = []
    for item in case.evidence.values():
        try:
            current = hash_file(item.file_path)
        except EvidenceError:
            problems.append(f"{item.evidence_id}: file is missing or unreadable.")
            continue
        if current != item.sha256:
            problems.append(f"{item.evidence_id}: file has been modified.")
    return problems


def check_integrity(case: Case) -> Tuple[bool, List[str]]:
    """Run both checks and return (everything_ok, messages)."""
    result = verify_chain(case)
    problems = verify_evidence_files(case)
    return result.ok and not problems, [result.message] + problems
