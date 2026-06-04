from mcp_server.db import fetch_all_pdb

for pdb_name in ["ORCLPDB1", "ORCLPDB2"]:
    print(f"\nTesting {pdb_name}")

    rows = fetch_all_pdb("""
        SELECT
            SYS_CONTEXT('USERENV', 'CON_NAME') AS container_name,
            SYS_CONTEXT('USERENV', 'SERVICE_NAME') AS service_name
        FROM dual
    """, pdb_name=pdb_name)

    print(rows)
