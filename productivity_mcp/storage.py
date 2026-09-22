"""Local JSON storage with safe public errors and detailed private logs."""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from productivity_mcp.config import settings


class StorageError(RuntimeError):
    """A safe error that can be returned without exposing internals."""


def _configure_logger() -> logging.Logger:
    """Create a local file logger for technical error details."""
    settings.log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("productivity_mcp")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(
            settings.log_directory / "server.log",
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = _configure_logger()


def initialize_storage() -> None:
    """Create application directories and the initial task file."""
    settings.data_directory.mkdir(parents=True, exist_ok=True)
    settings.log_directory.mkdir(parents=True, exist_ok=True)

    task_file = settings.data_directory / "tasks.json"

    if not task_file.exists():
        task_file.write_text("[]", encoding="utf-8")


def _read_tasks(task_file: Path) -> list[dict]:
    """Read existing tasks from disk."""
    content = task_file.read_text(encoding="utf-8")
    tasks = json.loads(content)

    if not isinstance(tasks, list):
        raise ValueError("Task storage must contain a JSON list.")

    return tasks


def save_task(
    title: str,
    due_date: str,
    priority: str,
    notes: str,
) -> dict:
    """Save one task and return its public record."""
    initialize_storage()
    task_file = settings.data_directory / "tasks.json"
    temporary_file = settings.data_directory / "tasks.tmp"

    task = {
        "id": str(uuid4()),
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "notes": notes,
        "created_at": datetime.now(UTC).isoformat(),
    }

    try:
        tasks = _read_tasks(task_file)
        tasks.append(task)

        temporary_file.write_text(
            json.dumps(tasks, indent=2),
            encoding="utf-8",
        )
        temporary_file.replace(task_file)
        return task
    except Exception:
        logger.exception("Internal failure while saving a task.")
        raise StorageError(
            "The task could not be saved. Check the local server log."
        ) from None


def save_email_draft(
    recipient_email: str,
    subject: str,
    body: str,
) -> dict:
    """Save an email draft using a server-generated safe filename."""
    initialize_storage()
    draft_id = str(uuid4())
    draft_directory = settings.data_directory / "drafts"
    draft_file = draft_directory / f"{draft_id}.json"

    draft = {
        "id": draft_id,
        "recipient_email": recipient_email,
        "subject": subject,
        "body": body,
        "created_at": datetime.now(UTC).isoformat(),
        "status": "draft",
    }

    try:
        draft_directory.mkdir(parents=True, exist_ok=True)
        draft_file.write_text(
            json.dumps(draft, indent=2),
            encoding="utf-8",
        )
        return draft
    except Exception:
        logger.exception("Internal failure while saving an email draft.")
        raise StorageError(
            "The email draft could not be saved. "
            "Check the local server log."
        ) from None