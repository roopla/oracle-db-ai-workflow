from fastmcp import FastMCP

from mcp_server.db import fetch_all_pdb


def register_storage_tools(mcp: FastMCP) -> None:
    @mcp.tool()
    def show_tablespace_usage(pdb_name: str | None = None) -> list[dict]:
        """
        Show tablespace size, used space, free space, and used percentage for selected PDB.
        """
        sql = """
            SELECT
                df.tablespace_name,
                ROUND(df.total_mb, 2) AS total_mb,
                ROUND(df.total_mb - NVL(fs.free_mb, 0), 2) AS used_mb,
                ROUND(NVL(fs.free_mb, 0), 2) AS free_mb,
                ROUND(((df.total_mb - NVL(fs.free_mb, 0)) / df.total_mb) * 100, 2) AS used_pct
            FROM
                (
                    SELECT tablespace_name, SUM(bytes) / 1024 / 1024 AS total_mb
                    FROM dba_data_files
                    GROUP BY tablespace_name
                ) df
            LEFT JOIN
                (
                    SELECT tablespace_name, SUM(bytes) / 1024 / 1024 AS free_mb
                    FROM dba_free_space
                    GROUP BY tablespace_name
                ) fs
            ON df.tablespace_name = fs.tablespace_name
            ORDER BY used_pct DESC
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)

    @mcp.tool()
    def show_datafiles(pdb_name: str | None = None) -> list[dict]:
        """
        Show datafiles for selected PDB.
        """
        sql = """
            SELECT
                file_id,
                file_name,
                tablespace_name,
                ROUND(bytes / 1024 / 1024, 2) AS size_mb,
                autoextensible,
                ROUND(maxbytes / 1024 / 1024, 2) AS max_size_mb,
                status
            FROM dba_data_files
            ORDER BY tablespace_name, file_id
        """
        return fetch_all_pdb(sql, pdb_name=pdb_name)
