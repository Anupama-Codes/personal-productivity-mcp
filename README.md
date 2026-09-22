# Personal Productivity MCP Server

A local Model Context Protocol (MCP) server written in Python for personal productivity. It allows an MCP client such as Claude Desktop to create tasks, generate email drafts, and access a daily productivity planning prompt.

## Features

- Create and locally store tasks with due dates, priorities, and notes.
- Create and locally store email drafts with recipient, subject, and body.
- Provide a reusable daily productivity planning prompt.
- Validate and sanitize user input.
- Hide sensitive internal error details from MCP clients.
- Store all data locally in JSON format.

> **Note:** The email-draft tool does not connect to Gmail or Outlook and does not send emails. Drafts are saved as JSON files in the local `data/drafts` directory.

## MCP Components

### Tools

#### `create_task`

Creates a task and saves it locally in `data/tasks.json`.

Inputs:

- `title`: Task title
- `due_date`: Due date in `YYYY-MM-DD` format
- `priority`: `low`, `medium`, or `high`
- `notes`: Optional task details

#### `create_email_draft`

Creates an email draft and saves it as a JSON file in `data/drafts`.

Inputs:

- `recipient_email`: Valid recipient email address
- `subject`: Email subject
- `body`: Email content

This tool only creates a local draft. It does not authenticate with an email provider or send an email.

### Prompt

#### `daily_productivity_plan`

Produces instructions for organizing a list of tasks into a productivity plan based on the number of available hours.

The prompt is registered by the MCP server. Some Claude Desktop versions display MCP tools but do not expose server prompts directly in the chat interface. Its registration can be verified with:

```powershell
python -c "import asyncio; from productivity_mcp.server import mcp; print([prompt.name for prompt in asyncio.run(mcp.list_prompts())])"
```

Expected output:

```text
['daily_productivity_plan']
```

## Project Structure

```text
Applied AI/
├── productivity_mcp/
│   ├── __init__.py
│   ├── config.py
│   ├── server.py
│   ├── storage.py
│   └── validators.py
├── tests/
│   └── test_security.py
├── data/                         # Generated local data; not committed
├── logs/                         # Generated server logs; not committed
├── .env                          # Local configuration; not committed
├── .env.example                  # Example configuration
├── .gitignore
├── claude_desktop_config.json
├── requirements.txt
├── run_server.py
└── README.md
```

## Requirements

- Python 3.12
- `uv`
- Claude Desktop for MCP integration
- Windows PowerShell commands are used in the setup instructions below

## Installation

Clone the repository and enter its directory:

```powershell
git clone https://github.com/Anupama-Codes/personal-productivity-mcp.git
cd "Applied AI"
```

Create a Python 3.12 virtual environment:

```powershell
uv venv --python 3.12
```

If PowerShell prevents script execution, allow activation for the current terminal session only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Activate the virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

Install the required packages:

```powershell
uv pip install -r requirements.txt
```

## Configuration

Copy the example configuration file:

```powershell
Copy-Item .env.example .env
```

The available settings are:

```env
PRODUCTIVITY_DATA_DIR=data
PRODUCTIVITY_LOG_DIR=logs
MAX_INPUT_LENGTH=2000
```

The application loads configuration from `.env` using `python-dotenv`. File locations are handled using `pathlib.Path`. The `.env` file is excluded from Git, while `.env.example` documents the required settings.

### Authentication and Secret Management

This server communicates with Claude Desktop locally through the MCP standard input/output (`stdio`) transport. It stores tasks and drafts on the local machine and does not connect to Gmail, Outlook, or another external API. Therefore, external API credentials are not currently required.

If an email-provider integration is added later, its credentials must be placed in `.env` and must never be committed to Git.

## Running the Server

Run the server from the project root:

```powershell
python .\run_server.py
```

A server using `stdio` waits for an MCP client to communicate through standard input and output. When launched manually, it may appear to do nothing. This is expected. Press `Ctrl+C` to stop it.

## Running the Tests

Run all tests from the project root:

```powershell
python -m pytest -v
```

The test suite verifies that:

- Path-traversal input is rejected.
- Email-header injection is rejected.
- Internal error details are not disclosed to the client.

## Security Best Practices

### 1. Input Sanitization

The server validates all user-provided values before saving them. The validation layer:

- Rejects empty required fields.
- Restricts the maximum input length.
- Rejects control characters.
- Rejects path-traversal patterns such as `../` and `..\`.
- Validates email-address syntax.
- Blocks newline characters in email fields to prevent email-header injection.
- Accepts only valid ISO dates and known priority values.

Example path-traversal attack:

```text
../../secret.txt
```

This input is rejected instead of being used as a task title or file location.

Example email-header injection attack:

```text
victim@example.com
Bcc: attacker@example.com
```

The newline and injected header are rejected by the input-validation layer.

### 2. Safe Error Disclosure

Detailed exceptions are written only to the local server log. MCP clients receive a generic error response, preventing the disclosure of:

- Local file paths
- Stack traces
- Environment details
- Internal implementation information
- Potential credentials

For example, an internal exception containing a sensitive local path is logged locally, while the client receives a message such as:

```text
An internal error occurred while creating the task.
```

The security tests demonstrate that the sensitive exception content is not returned to the MCP client.

## Claude Desktop Configuration

The repository includes `claude_desktop_config.json`. Its Windows paths must be changed to match the location where the repository and virtual environment are installed.

Example:

```json
{
  "mcpServers": {
    "personal-productivity-mcp": {
      "command": "C:\\Users\\YOUR_USERNAME\\path\\to\\project\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\YOUR_USERNAME\\path\\to\\project\\run_server.py"
      ]
    }
  }
}
```

To configure Claude Desktop:

1. Open Claude Desktop.
2. Open **Settings**.
3. Select **Developer**.
4. Select **Edit config**.
5. Add the `personal-productivity-mcp` entry under `mcpServers`.
6. Save the configuration.
7. Fully close Claude Desktop, including its background process.
8. Reopen Claude Desktop.
9. Confirm that `personal-productivity-mcp` displays the status **Running**.

The repository configuration contains the complete entry used during development. Another user must replace the absolute Windows paths with paths from their own computer.

## Example Usage

After the server is running through Claude Desktop, a user can request:

```text
Use the personal-productivity-mcp tool to create a high-priority task called
"Prepare MCP demo" due on 2026-09-30, with the note
"Demonstrate the tools and security tests."
```

The client will request permission before running the tool. The resulting task is stored in `data/tasks.json`.

An email-draft request can be written as:

```text
Use the personal-productivity-mcp tool to create an email draft to
professor@example.com with the subject "MCP Demo Ready" and the body
"Hello Professor, my personal productivity MCP server is ready for demonstration."
```

The resulting draft is stored locally in `data/drafts`. It will not appear in an email account because the server does not connect to an email provider.

## Limitations

- Tasks and drafts are stored only on the local machine.
- Email drafts are not synchronized with or sent through an email provider.
- The server does not currently update, delete, or list saved items.
- JSON storage is suitable for a small demonstration but not concurrent, large-scale use.
- Rate limiting is not implemented because the selected best practices are input sanitization and safe error disclosure.
- MCP prompt visibility depends on the capabilities of the MCP client.
- The Claude Desktop configuration contains machine-specific absolute paths.

Possible future improvements include authenticated Gmail or Outlook integration, encrypted credential storage, SQLite persistence, task-management operations, rate limiting, and additional automated tests.

## References and Code Citations

The MCP server structure and decorator-based registration approach were adapted from the official Model Context Protocol Python SDK documentation and examples:

- Model Context Protocol documentation: <https://modelcontextprotocol.io/>
- MCP Python SDK: <https://github.com/modelcontextprotocol/python-sdk>
- MCP example servers: <https://github.com/modelcontextprotocol/servers>
- `python-dotenv` documentation: <https://github.com/theskumar/python-dotenv>
- `email-validator` documentation: <https://github.com/JoshData/python-email-validator>

Relevant source files also contain comments identifying code patterns adapted from external documentation. The implementation was developed with assistance from an AI assistant and was reviewed and tested locally by the author.