import asyncio

from dotenv import load_dotenv
from agents import set_tracing_disabled

from agent_app.oracle_agent_runner import (
    clear_oracle_agent_session,
    run_oracle_agent,
)


CLI_SESSION_ID = "cli_default"


async def main() -> None:
    load_dotenv()
    set_tracing_disabled(True)

    print("Oracle DBA AI Agent - Agents SDK")
    print("Type 'exit' or 'quit' to stop.")
    print("Type 'clear', 'clear history', 'reset', or 'reset session' to clear memory.\n")

    while True:
        user_input = input("Ask OracleDB AI: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            await clear_oracle_agent_session("cli_default")
            print("Session history cleared. Goodbye.\n")
            break

        if not user_input:
            continue

        if user_input.lower() in {"clear", "clear history", "reset", "reset session"}:
            await clear_oracle_agent_session(CLI_SESSION_ID)
            print("Session history cleared.\n")
            continue

        try:
            result = await run_oracle_agent(
                user_input=user_input,
                interface="cli",
                session_id=CLI_SESSION_ID,
                max_turns=20,
            )

            print("\nTool calls:")

            if result["tool_calls"]:
                for call in result["tool_calls"]:
                    print(f"Selected MCP tool: {call['tool']}")
                    print(f"Tool arguments: {call['arguments']}")
                    print("Tool returned output.")
            else:
                print("No MCP tool was used.")

            print("\nFinal answer:")
            print(result["answer"])
            print("\n" + "-" * 80 + "\n")

        except Exception as exc:
            print("\nERROR:")
            print(str(exc))
            print("\n" + "-" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
