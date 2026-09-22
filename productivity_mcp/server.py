"""Personal Productivity MCP server."""

from datetime import date

from mcp.server.mcpserver import MCPServer

from productivity_mcp.storage import (
    StorageError,
    initialize_storage,
    save_email_draft,
    save_task,
)
from productivity_mcp.validators import (
    InputValidationError,
    sanitize_email_address,
    sanitize_text,
)


# MCPServer structure and decorators follow the official MCP Python SDK:
# https://github.com/modelcontextprotocol/python-sdk
mcp = MCPServer(
    "personal-productivity-mcp",
    title="Personal Productivity MCP",
    description="Creates local tasks and email drafts.",
    version="1.0.0",
)

_ALLOWED_PRIORITIES = {"low", "medium", "high"}


def _sanitize_optional_notes(notes: str) -> str:
    """Allow empty notes while sanitizing any supplied content."""
    if not isinstance(notes, str):
        raise InputValidationError("notes must be text.")

    if not notes.strip():
        return ""

    return sanitize_text(
        notes,
        "notes",
        allow_newlines=True,
    )


def _validate_due_date(due_date: str) -> str:
    """Require an ISO date in YYYY-MM-DD format."""
    cleaned = sanitize_text(due_date, "due_date")

    try:
        date.fromisoformat(cleaned)
    except ValueError as exc:
        raise InputValidationError(
            "due_date must use YYYY-MM-DD format."
        ) from exc

    return cleaned


def _validate_priority(priority: str) -> str:
    """Allow only the documented task priorities."""
    cleaned = sanitize_text(priority, "priority").lower()

    if cleaned not in _ALLOWED_PRIORITIES:
        raise InputValidationError(
            "priority must be low, medium, or high."
        )

    return cleaned


@mcp.tool()
def create_task(
    title: str,
    due_date: str,
    priority: str = "medium",
    notes: str = "",
) -> dict:
    """Create and locally save a task with a due date and priority."""
    try:
        clean_title = sanitize_text(title, "title")
        clean_due_date = _validate_due_date(due_date)
        clean_priority = _validate_priority(priority)
        clean_notes = _sanitize_optional_notes(notes)

        task = save_task(
            title=clean_title,
            due_date=clean_due_date,
            priority=clean_priority,
            notes=clean_notes,
        )

        return {
            "success": True,
            "message": "Task created successfully.",
            "task": task,
        }
    except InputValidationError as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    except StorageError as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    except Exception:
        return {
            "success": False,
            "error": "An unexpected error occurred while creating the task.",
        }


@mcp.tool()
def create_email_draft(
    recipient_email: str,
    subject: str,
    body: str,
) -> dict:
    """Create and locally save an email draft without sending it."""
    try:
        clean_email = sanitize_email_address(recipient_email)
        clean_subject = sanitize_text(subject, "subject")
        clean_body = sanitize_text(
            body,
            "body",
            allow_newlines=True,
        )

        draft = save_email_draft(
            recipient_email=clean_email,
            subject=clean_subject,
            body=clean_body,
        )

        return {
            "success": True,
            "message": "Email draft created successfully.",
            "draft": draft,
        }
    except InputValidationError as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    except StorageError as exc:
        return {
            "success": False,
            "error": str(exc),
        }
    except Exception:
        return {
            "success": False,
            "error": (
                "An unexpected error occurred while creating "
                "the email draft."
            ),
        }


@mcp.prompt()
def daily_productivity_plan(
    tasks: str,
    available_hours: float = 8,
) -> str:
    """Create instructions for organizing a practical daily work plan."""
    clean_tasks = sanitize_text(
        tasks,
        "tasks",
        allow_newlines=True,
    )

    if available_hours <= 0 or available_hours > 24:
        raise ValueError("available_hours must be between 0 and 24.")

    return f"""
Act as a practical productivity assistant.

The user has {available_hours} available hours today.

Tasks:
{clean_tasks}

Create a realistic daily plan that:
1. Prioritizes urgent and high-impact work.
2. Includes focused work blocks and short breaks.
3. Identifies tasks that may need an email follow-up.
4. Suggests using create_task for any missing action items.
5. Suggests using create_email_draft when communication is needed.
6. Does not claim that an email was sent because this server only saves drafts.
""".strip()


def main() -> None:
    """Initialize storage and run the MCP server over standard input/output."""
    initialize_storage()
    mcp.run()


if __name__ == "__main__":
    main()