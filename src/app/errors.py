class DomainError(Exception):
    """Base class for domain-level errors."""


class ValidationError(DomainError):
    """Raised when input validation fails."""


class StorageError(DomainError):
    """Raised when DB operations fail."""


class ExtractError(DomainError):
    """Raised when Telegram extraction fails."""


class SummarizeError(DomainError):
    """Raised when LLM summarization fails."""
