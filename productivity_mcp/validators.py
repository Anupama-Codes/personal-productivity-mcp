"""Validation helpers for all untrusted tool inputs."""

import re

from email_validator import EmailNotValidError, validate_email

from productivity_mcp.config import settings


class InputValidationError(ValueError):
    """Raised when a tool receives unsafe or invalid input."""


_CONTROL_CHARACTERS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]"
)
_PATH_TRAVERSAL = re.compile(
    r"(^|[\\/])\.\.([\\/]|$)"
)


def sanitize_text(
    value: str,
    field_name: str,
    *,
    allow_newlines: bool = False,
) -> str:
    """Validate and normalize user-provided text."""
    if not isinstance(value, str):
        raise InputValidationError(f"{field_name} must be text.")

    cleaned = value.strip()

    if not cleaned:
        raise InputValidationError(f"{field_name} cannot be empty.")

    if len(cleaned) > settings.maximum_input_length:
        raise InputValidationError(
            f"{field_name} exceeds the permitted length."
        )

    if _CONTROL_CHARACTERS.search(cleaned):
        raise InputValidationError(
            f"{field_name} contains unsupported control characters."
        )

    if _PATH_TRAVERSAL.search(cleaned):
        raise InputValidationError(
            f"{field_name} contains an unsafe path sequence."
        )

    if not allow_newlines and ("\n" in cleaned or "\r" in cleaned):
        raise InputValidationError(
            f"{field_name} must be a single line."
        )

    return cleaned


def sanitize_email_address(value: str) -> str:
    """Validate and normalize an email address."""
    cleaned = sanitize_text(value, "recipient_email")

    try:
        result = validate_email(
            cleaned,
            check_deliverability=False,
        )
    except EmailNotValidError as exc:
        raise InputValidationError(
            "recipient_email is not a valid email address."
        ) from exc

    return result.normalized