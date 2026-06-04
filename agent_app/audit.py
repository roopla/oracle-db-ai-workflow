import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOG_DIR = Path(os.getenv("AUDIT_LOG_DIR", "logs"))
LOG_FILE = LOG_DIR / "agent_audit.log"

LOG_FINAL_ANSWER = os.getenv("AUDIT_LOG_FINAL_ANSWER", "false").lower() == "true"


def write_audit_log(
    *,
    interface: str,
    user_input: str,
    tool_calls: list[dict[str, Any]],
    status: str = "success",
    error: str | None = None,
    duration_ms: int | None = None,
    final_answer: str | None = None,
) -> None:
    """
    Write one JSON audit entry per agent request.

    By default, this does not log the final LLM answer because the answer may contain
    database object names, users, schema names, session details, or other sensitive data.

    To enable final answer logging for local/dev testing only, set:
        AUDIT_LOG_FINAL_ANSWER=true
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    entry: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "interface": interface,
        "user_input": user_input,
        "tool_calls": tool_calls,
        "status": status,
    }

    if duration_ms is not None:
        entry["duration_ms"] = duration_ms

    if error:
        entry["error"] = error

    if LOG_FINAL_ANSWER and final_answer is not None:
        entry["final_answer"] = final_answer

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")