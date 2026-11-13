# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Creating cases and managing the evidence inside them."""

from core.errors import EvidenceError
from core.hashing import hash_file
from core.models import Case, EvidenceItem
from core.validation import require_text, utc_now, validate_evidence_id


def create_case(case_id: str, title: str, investigator: str) -> Case:
    """Create an empty case after checking the inputs."""
    return Case(
        case_id=require_text(case_id, "Case ID"),
        title=require_text(title, "Title"),
        investigator=require_text(investigator, "Investigator"),
        created_at=utc_now(),
    )


def register_evidence(
    case: Case,
    evidence_id: str,
    description: str,
    source: str,
    collector: str,
    file_path: str,
) -> EvidenceItem:
    """Hash a file and add it to the case as an evidence item."""
    clean_id = validate_evidence_id(evidence_id, case.evidence)
    item = EvidenceItem(
        evidence_id=clean_id,
        description=require_text(description, "Description"),
        source=require_text(source, "Source"),
        collector=require_text(collector, "Collector"),
        file_path=require_text(file_path, "File path"),
        sha256="",
        added_at=utc_now(),
    )
    item.sha256 = hash_file(item.file_path)
    case.evidence[clean_id] = item
    return item


def get_evidence(case: Case, evidence_id: str) -> EvidenceItem:
    """Look up one evidence item by its ID."""
    try:
        return case.evidence[(evidence_id or "").strip()]
    except KeyError:
        raise EvidenceError(f"No evidence with ID '{evidence_id}'.") from None


def edit_evidence_description(case: Case, evidence_id: str, new_text: str) -> None:
    """Change the description of an evidence item."""
    item = get_evidence(case, evidence_id)
    item.description = require_text(new_text, "Description")


def delete_evidence(case: Case, evidence_id: str) -> None:
    """Remove an evidence item from the case."""
    item = get_evidence(case, evidence_id)
    del case.evidence[item.evidence_id]
