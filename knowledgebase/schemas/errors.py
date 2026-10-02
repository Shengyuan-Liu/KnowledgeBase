"""Errors shared across storage, services, and transport adapters."""


class FileRecordNotFoundError(LookupError):
    """A requested file record does not exist in business storage."""
