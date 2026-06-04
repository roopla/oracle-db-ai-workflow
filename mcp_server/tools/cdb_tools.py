from fastmcp import FastMCP

from mcp_server.db import fetch_all_cdb


def register_cdb_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def check_db_status() -> list[dict]:
        """
        Show basic CDB/root Oracle instance and database status.

        This is a CDB-level tool.
        """
        sql = """
            SELECT
                i.instance_name,
                i.host_name,
                i.status AS instance_status,
                d.name AS database_name,
                d.open_mode,
                d.database_role
            FROM v$instance i
            CROSS JOIN v$database d
        """
        return fetch_all_cdb(sql)

    @mcp.tool()
    def list_pdbs() -> list[dict]:
        """
        List pluggable databases and open mode.

        This connects to CDB/root because PDB discovery should be done at the CDB level.
        """
        sql = """
            SELECT
                name,
                open_mode,
                restricted
            FROM v$pdbs
            ORDER BY name
        """
        return fetch_all_cdb(sql)
