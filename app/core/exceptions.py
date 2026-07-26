"""Application-wide exception hierarchy.

Every custom exception carries a stable `code` so the API layer can convert
it into a structured error response without leaking internals.
"""

from __future__ import annotations


class AppError(Exception):
    """Base class for all application-raised errors."""

    code: str = "app_error"
    http_status: int = 500

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class ValidationError(AppError):
    code = "validation_error"
    http_status = 400


class NotFoundError(AppError):
    code = "not_found"
    http_status = 404


class AuthenticationError(AppError):
    code = "authentication_error"
    http_status = 401


class LLMProviderError(AppError):
    code = "llm_provider_error"
    http_status = 502


class SheetsIntegrationError(AppError):
    code = "sheets_integration_error"
    http_status = 502


class TelegramIntegrationError(AppError):
    code = "telegram_integration_error"
    http_status = 502


class DuplicateRequestError(AppError):
    """Raised internally when a webhook delivery is a retry of a completed request."""

    code = "duplicate_request"
    http_status = 200
