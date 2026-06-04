import os
from pathlib import Path


def get_secret(name: str, default: str | None = None) -> str | None:
    """
    Read a secret from either:
    1. NAME_FILE=/run/secrets/something
    2. NAME=value

    Supports both local development and Docker secrets.
    """
    file_path = os.getenv(f"{name}_FILE")

    if file_path:
        path = Path(file_path)

        if not path.exists():
            raise RuntimeError(f"Secret file does not exist for {name}: {file_path}")

        return path.read_text(encoding="utf-8").strip()

    return os.getenv(name, default)
