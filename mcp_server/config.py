import os
from dataclasses import dataclass


@dataclass(frozen=True)
class OracleConfig:
    host: str
    port: str
    user: str | None
    cdb_service: str | None
    default_pdb: str | None
    dsn: str | None
    service_suffix: str


@dataclass(frozen=True)
class McpConfig:
    host: str
    port: int
    path: str


def get_oracle_config() -> OracleConfig:
    return OracleConfig(
        host=os.getenv("ORACLE_HOST", "localhost"),
        port=os.getenv("ORACLE_PORT", "1521"),
        user=os.getenv("ORACLE_USER"),
        cdb_service=os.getenv("ORACLE_CDB_SERVICE"),
        default_pdb=os.getenv("ORACLE_DEFAULT_PDB"),
        dsn=os.getenv("ORACLE_DSN"),
        service_suffix=os.getenv("ORACLE_SERVICE_SUFFIX", ".localdomain"),
    )


def get_mcp_config() -> McpConfig:
    return McpConfig(
        host=os.getenv("MCP_HOST", "0.0.0.0"),
        port=int(os.getenv("MCP_PORT", "9000")),
        path=os.getenv("MCP_PATH", "/mcp"),
    )
