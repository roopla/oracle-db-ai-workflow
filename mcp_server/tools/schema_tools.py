from fastmcp import FastMCP

from mcp_server.db import fetch_all_pdb


def register_schema_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def show_schema_sizes(pdb_name: str | None = None) -> list[dict]:
        """
        Show schema sizes in MB for selected PDB.
        """
        sql = """
            SELECT
                owner AS schema_name,
                ROUND(SUM(bytes) / 1024 / 1024, 2) AS size_mb
            FROM dba_segments
            GROUP BY owner
            ORDER BY size_mb DESC
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)

    @mcp.tool()
    def show_database_users(pdb_name: str | None = None) -> list[dict]:
        """
        Show database users/accounts in selected PDB.
        """
        sql = """
            SELECT
                username,
                account_status,
                default_tablespace,
                temporary_tablespace,
                created,
                common,
                oracle_maintained
            FROM dba_users
            ORDER BY oracle_maintained, username
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)

    @mcp.tool()
    def show_invalid_objects(
        owner: str | None = None,
        pdb_name: str | None = None,
    ) -> list[dict]:
        """
        Show invalid database objects in selected PDB.
        Optionally filter by owner/schema.
        """
        sql = """
            SELECT
                owner,
                object_name,
                object_type,
                status,
                last_ddl_time
            FROM dba_objects
            WHERE status <> 'VALID'
              AND (:owner IS NULL OR owner = UPPER(:owner))
            ORDER BY owner, object_type, object_name
        """
        return fetch_all_pdb(sql, {"owner": owner}, pdb_name=pdb_name)
