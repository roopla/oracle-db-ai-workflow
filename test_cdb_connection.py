from mcp_server.db import fetch_all_cdb

rows = fetch_all_cdb("""
    SELECT
        name,
        open_mode,
        database_role
    FROM v$database
""")

print(rows)
