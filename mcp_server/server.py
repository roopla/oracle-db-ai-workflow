import sys
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mcp_server.config import get_mcp_config
from mcp_server.tools.cdb_tools import register_cdb_tools
from mcp_server.tools.parameter_tools import register_parameter_tools
from mcp_server.tools.schema_tools import register_schema_tools
from mcp_server.tools.session_tools import register_session_tools
from mcp_server.tools.storage_tools import register_storage_tools

load_dotenv()

mcp = FastMCP("Oracle DBA MCP Server")


def register_tools() -> None:
    register_cdb_tools(mcp)
    register_parameter_tools(mcp)
    register_storage_tools(mcp)
    register_session_tools(mcp)
    register_schema_tools(mcp)


register_tools()


if __name__ == "__main__":
    config = get_mcp_config()

    mcp.run(
        transport="http",
        host=config.host,
        port=config.port,
        path=config.path,
    )
