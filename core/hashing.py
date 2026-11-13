# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.

"""SHA-256 hashing helpers."""

import hashlib

from core.errors import EvidenceError


def hash_file(path: str, chunk_size: int = 8192) -> str:
    """Return the SHA-256 hex digest of a file, reading it in chunks."""
    sha = hashlib.sha256()
    try:
        with open(path, "rb") as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                sha.update(chunk)
    except OSError as err:
        raise EvidenceError(f"Cannot read file '{path}': {err}") from err
    return sha.hexdigest()


def hash_text(text: str) -> str:
    """Return the SHA-256 hex digest of a piece of text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


