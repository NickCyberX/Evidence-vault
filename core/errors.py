# I acknowledge the use of Claude (Anthropic, https://claude.ai) to review the code in this file.
"""Custom error types used across the Evidence Vault core."""


class VaultError(Exception):
    """Base class for every error the vault raises on purpose."""


class ValidationError(VaultError):
    """Raised when user input is not acceptable."""


class StorageError(VaultError):
    """Raised when a file cannot be saved, loaded or imported."""


class EvidenceError(VaultError):
    """Raised when an evidence item or evidence file has a problem."""
