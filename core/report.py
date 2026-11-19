# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Text report and CSV export for a case."""

import csv

from core.chain import check_integrity
from core.errors import StorageError
from core.models import Case


def generate_text_report(case: Case) -> str:
    """Build a plain-text summary of the case."""
    ok, messages = check_integrity(case)
    lines = [
        f"CASE REPORT: {case.case_id} - {case.title}",
        f"Investigator: {case.investigator}",
        f"Created: {case.created_at}",
        "",
        f"Evidence items: {len(case.evidence)}",
    ]
    for item in sorted(case.evidence.values(), key=lambda i: i.evidence_id):
        lines.append(
            f"  - {item.evidence_id}: {item.description} (SHA-256 {item.sha256})"
        )
    lines += [
        "",
        f"Custody entries: {len(case.custody_log)}",
        f"Integrity: {'PASS' if ok else 'FAIL'}",
    ]
    lines += [f"  * {message}" for message in messages]
    lines += ["", f"Timeline events: {len(case.events)}"]
    if case.events:
        lines.append(f"  First: {case.events[0].timestamp}")
        lines.append(f"  Last:  {case.events[-1].timestamp}")
    return "\n".join(lines)
