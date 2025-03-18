"""
Custom exceptions for the application.
"""


class ApplicationError(Exception):
    """Base class for all application exceptions."""
    pass


class InvalidOperationError(ApplicationError):
    """Raised when an operation is invalid in the current context."""
    pass


class ResourceNotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""
    pass


class AuthorizationError(ApplicationError):
    """Raised when an operation is not authorized."""
    pass


class ValidationError(ApplicationError):
    """Raised when validation of data fails."""
    pass


class ConfigurationError(ApplicationError):
    """Raised when there is an issue with configuration."""
    pass


class ExternalServiceError(ApplicationError):
    """Raised when there is an issue with an external service."""
    pass


class ConcurrencyError(ApplicationError):
    """Raised when there is a concurrency issue."""
    pass 