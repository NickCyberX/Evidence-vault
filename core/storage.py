# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""Saving and loading a case as a JSON file."""

import json

from core.errors import StorageError
from core.models import Case, case_from_dict, case_to_dict


def save_case(case: Case, path: str) -> None:
    """Write the case to a JSON file."""
    try:
        with open(path, "w", encoding="utf-8") as file:
            json.dump(case_to_dict(case), file, indent=2)
    except OSError as err:
        raise StorageError(f"Could not save to '{path}': {err}") from err
