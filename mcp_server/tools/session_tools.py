from fastmcp import FastMCP

from mcp_server.db import fetch_all_pdb


def register_session_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def show_sessions_by_user(pdb_name: str | None = None) -> list[dict]:
        """
        Show session count grouped by database user for selected PDB.

        If pdb_name is not provided, uses default PDB.
        """
        sql = """
            SELECT
                NVL(username, 'BACKGROUND') AS username,
                status,
                COUNT(*) AS session_count
            FROM v$session
            GROUP BY NVL(username, 'BACKGROUND'), status
            ORDER BY session_count DESC
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)

    @mcp.tool()
    def show_blocking_sessions(pdb_name: str | None = None) -> list[dict]:
        """
        Show sessions that are waiting on blocking sessions in selected PDB.
        """
        sql = """
            SELECT
                sid,
                serial# AS serial_number,
                username,
                status,
                blocking_session,
                event,
                seconds_in_wait,
                machine,
                program
            FROM v$session
            WHERE blocking_session IS NOT NULL
            ORDER BY seconds_in_wait DESC
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)
