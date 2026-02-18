# FILE: src/app/errors.py
# VERSION: 1.0.0
# START_MODULE_CONTRACT
#   PURPOSE: Define domain-specific exception hierarchy used across application layers.
#   SCOPE: Provide semantic error classes for validation, storage, extraction, and summarization failures.
#   DEPENDS: none
#   LINKS: docs/development-plan.xml#M-ERRORS, docs/knowledge-graph.xml#M-ERRORS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   DomainError — Base class for domain-level failures.
#   ValidationError — Input validation failure.
#   StorageError — Persistence operation failure.
#   ExtractError — Telegram extractor/integration failure.
#   SummarizeError — LLM summarization/integration failure.
# END_MODULE_MAP
#
# START_CHANGE_SUMMARY
#   LAST_CHANGE: v1.0.0 - Added GRACE module contract and map.
# END_CHANGE_SUMMARY


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
