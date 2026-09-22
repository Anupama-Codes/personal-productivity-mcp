"""Load local configuration safely from the project's .env file."""

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Reference: python-dotenv documentation
# https://github.com/theskumar/python-dotenv
_ENV = dotenv_values(ENV_FILE)


def _safe_project_directory(setting_name: str, default: str) -> Path:
    """Resolve a configured directory and keep it inside the project folder."""
    raw_value = _ENV.get(setting_name) or default
    directory = (PROJECT_ROOT / raw_value).resolve()

    try:
        directory.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise RuntimeError(
            f"{setting_name} must point to a directory inside the project."
        ) from exc

    return directory


def _maximum_input_length() -> int:
    """Read and validate the maximum permitted input length."""
    raw_value = _ENV.get("MAX_INPUT_LENGTH") or "2000"

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError("MAX_INPUT_LENGTH must be an integer.") from exc

    if value < 100 or value > 10_000:
        raise RuntimeError("MAX_INPUT_LENGTH must be between 100 and 10000.")

    return value


@dataclass(frozen=True)
class Settings:
    """Application configuration."""

    data_directory: Path
    log_directory: Path
    maximum_input_length: int


settings = Settings(
    data_directory=_safe_project_directory(
        "PRODUCTIVITY_DATA_DIR", "data"
    ),
    log_directory=_safe_project_directory(
        "PRODUCTIVITY_LOG_DIR", "logs"
    ),
    maximum_input_length=_maximum_input_length(),
)