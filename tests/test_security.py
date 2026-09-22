"""Exploit checks for input sanitization and safe error disclosure."""

import productivity_mcp.server as server


def test_path_traversal_exploit_is_blocked() -> None:
    """A path traversal payload must be rejected before storage."""
    result = server.create_task(
        title="../../secret.txt",
        due_date="2026-09-30",
        priority="high",
        notes="Malicious path traversal attempt",
    )

    assert result["success"] is False
    assert "unsafe path sequence" in result["error"]


def test_email_header_injection_is_blocked() -> None:
    """A newline-based email header injection must be rejected."""
    malicious_email = (
        "victim@example.com\n"
        "Bcc: attacker@example.com"
    )

    result = server.create_email_draft(
        recipient_email=malicious_email,
        subject="Normal subject",
        body="Normal body",
    )

    assert result["success"] is False
    assert "single line" in result["error"]


def test_internal_error_details_are_not_disclosed(
    monkeypatch,
) -> None:
    """Sensitive exception details must not reach the MCP client."""
    sensitive_message = (
        "PermissionError at "
        r"C:\Users\Anupama T\private\credentials.txt"
    )

    def simulated_storage_failure(**kwargs):
        raise RuntimeError(sensitive_message)

    monkeypatch.setattr(
        server,
        "save_task",
        simulated_storage_failure,
    )

    result = server.create_task(
        title="Safe task",
        due_date="2026-09-30",
        priority="medium",
        notes="Trigger the simulated storage failure",
    )

    assert result["success"] is False
    assert result["error"] == (
        "An unexpected error occurred while creating the task."
    )
    assert sensitive_message not in str(result)
    assert "credentials.txt" not in str(result)