from fastmcp import FastMCP

from mcp_server.db import fetch_all_pdb


def register_parameter_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def check_db_version(pdb_name: str | None = None) -> list[dict]:
        """
        Show Oracle database version banner.

        If pdb_name is provided, connects to that PDB.
        If pdb_name is not provided, connects to the default PDB.
        """
        sql = """
            SELECT banner
            FROM v$version
            WHERE banner LIKE 'Oracle Database%'
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)

    @mcp.tool()
    def show_current_container(pdb_name: str | None = None) -> list[dict]:
        """
        Show the current Oracle container name for the selected connection.

        Useful for proving which PDB the tool connected to.
        """
        sql = """
            SELECT
                SYS_CONTEXT('USERENV', 'CON_NAME') AS container_name,
                SYS_CONTEXT('USERENV', 'SERVICE_NAME') AS service_name,
                SYS_CONTEXT('USERENV', 'DB_NAME') AS db_name
            FROM dual
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)

    @mcp.tool()
    def show_parameters(
        parameter_name: str = "",
        pdb_name: str | None = None,
    ) -> list[dict]:
        """
        Show Oracle initialization parameters for the selected PDB connection.

        Args:
            parameter_name: Optional parameter name filter. Examples: sga, pga, memory, sessions, processes, open_cursors.
            pdb_name: Optional PDB name. If omitted, connects to the default PDB.

        Example requests:
            - show parameters for sga -> parameter_name='sga'
            - show parameters for pga -> parameter_name='pga'
            - show parameters for memory -> parameter_name='memory'
            - show parameter processes -> parameter_name='processes'
            - show parameter open_cursors -> parameter_name='open_cursors'
        """
        sql = """
            SELECT
                name,
                value,
                display_value,
                description
            FROM v$parameter
            WHERE :parameter_name IS NULL
            OR :parameter_name = ''
            OR LOWER(name) LIKE LOWER(:parameter_name)
            ORDER BY name
        """

        return fetch_all_pdb(
            sql,
            {"parameter_name": f"%{parameter_name}%"},
            pdb_name=pdb_name,
        )