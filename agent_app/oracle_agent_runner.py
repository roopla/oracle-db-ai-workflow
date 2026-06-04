import os
import time
from pathlib import Path
from typing import Any

import httpx
from openai import AsyncOpenAI

from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStreamableHttp
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

from agent_app.audit import write_audit_log
from agent_app.prompts.oracle_dba_agent_prompt import ORACLE_DBA_AGENT_INSTRUCTIONS


def _get_cert_file() -> str | bool:
    return (
        os.getenv("SSL_CERT_FILE")
        or os.getenv("REQUESTS_CA_BUNDLE")
        or True
    )


def _get_openwebui_config() -> tuple[str, str, str]:
    openwebui_base_url = os.getenv("OPENWEBUI_BASE_URL")
    openwebui_api_key = os.getenv("OPENWEBUI_API_KEY")
    model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    if not openwebui_base_url:
        raise RuntimeError("OPENWEBUI_BASE_URL is missing in .env")

    if not openwebui_api_key:
        raise RuntimeError("OPENWEBUI_API_KEY is missing in .env")

    return openwebui_base_url, openwebui_api_key, model_name


def _build_session(session_id: str) -> SQLiteSession:
    """
    Build SQLite-backed session memory for follow-up questions.
    Same session_id = same conversation memory.
    """
    Path("data").mkdir(parents=True, exist_ok=True)

    return SQLiteSession(
        session_id,
        "data/agent_sessions.db",
    )


async def clear_oracle_agent_session(session_id: str = "default") -> None:
    """
    Clear conversation memory for one session.

    This clears the OpenAI Agents SDK SQLiteSession history for the given
    session_id. It does not delete audit logs and does not change the browser UI
    unless the web client also clears the visible chat.
    """
    session = _build_session(session_id)
    await session.clear_session()


def extract_tool_calls(result: Any) -> list[dict[str, str]]:
    tool_calls: list[dict[str, str]] = []

    for item in result.new_items:
        if type(item).__name__ == "ToolCallItem":
            raw = item.raw_item
            tool_calls.append(
                {
                    "tool": getattr(raw, "name", "unknown"),
                    "arguments": getattr(raw, "arguments", "{}"),
                }
            )

    return tool_calls


async def run_oracle_agent(
    *,
    user_input: str,
    interface: str,
    session_id: str = "default",
    max_turns: int = 20,
) -> dict[str, Any]:
    """
    Shared Oracle DBA agent runner used by both CLI and web.

    This function performs the full flow:
    - Build OpenWebUI-compatible Chat Completions model
    - Connect to the MCP server
    - Create the Oracle DBA Agent
    - Create/load SQLite session memory
    - Run the agent with the user's input
    - Extract MCP tool calls
    - Write audit log
    - Return final answer and tool metadata
    """
    mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:9000/mcp")
    openwebui_base_url, openwebui_api_key, model_name = _get_openwebui_config()

    tool_calls: list[dict[str, str]] = []
    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(verify=_get_cert_file()) as http_client:
            openai_client = AsyncOpenAI(
                api_key=openwebui_api_key,
                base_url=openwebui_base_url,
                http_client=http_client,
            )

            model = OpenAIChatCompletionsModel(
                model=model_name,
                openai_client=openai_client,
            )

            async with MCPServerStreamableHttp(
                name="Oracle DBA MCP Server",
                params={"url": mcp_server_url},
                client_session_timeout_seconds=30,
            ) as oracle_mcp:
                agent = Agent(
                    name="Oracle DBA Assistant",
                    instructions=ORACLE_DBA_AGENT_INSTRUCTIONS,
                    model=model,
                    mcp_servers=[oracle_mcp],
                    mcp_config={
                        "convert_schemas_to_strict": True,
                        "failure_error_function": None,
                    },
                )

                session = _build_session(session_id)

                result = await Runner.run(
                    agent,
                    user_input,
                    max_turns=max_turns,
                    session=session,
                )

        duration_ms = int((time.perf_counter() - start_time) * 1000)
        tool_calls = extract_tool_calls(result)

        write_audit_log(
            interface=interface,
            user_input=user_input,
            tool_calls=tool_calls,
            status="success",
            duration_ms=duration_ms,
            final_answer=result.final_output,
        )

        return {
            "answer": result.final_output,
            "tool_calls": tool_calls,
            "duration_ms": duration_ms,
            "session_id": session_id,
        }

    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        write_audit_log(
            interface=interface,
            user_input=user_input,
            tool_calls=tool_calls,
            status="error",
            error=str(exc),
            duration_ms=duration_ms,
        )

        raise
