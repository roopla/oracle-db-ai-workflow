import os

from contextlib import contextmanager

import oracledb
from dotenv import load_dotenv

from mcp_server.config import get_oracle_config
from mcp_server.secret_utils import get_secret

load_dotenv()

def db_debug(message: str) -> None:
    if os.getenv("DB_DEBUG", "false").lower() == "true":
        print(f"[DB DEBUG] {message}", flush=True)

    


def normalize_service_name(service_name: str) -> str:
    """
    Normalize Oracle service names.

    Uses ORACLE_SERVICE_SUFFIX when the service name does not already contain a dot.

    Examples with ORACLE_SERVICE_SUFFIX=.localdomain:
    ORCLPDB1              -> orclpdb1.localdomain
    orclpdb2              -> orclpdb2.localdomain
    orclpdb1.localdomain  -> orclpdb1.localdomain

    Examples with ORACLE_SERVICE_SUFFIX empty:
    ORCLPDB1              -> orclpdb1
    """
    config = get_oracle_config()

    service_name = service_name.strip()

    if not service_name:
        raise RuntimeError("Oracle service name cannot be empty.")

    if "." not in service_name and config.service_suffix:
        service_name = f"{service_name.lower()}{config.service_suffix}"

    return service_name.lower()






def build_cdb_dsn() -> str:
    """
    Build DSN for CDB/root connection.

    Used for:
    - list_pdbs
    - CDB/database status
    - PDB discovery
    """
    config = get_oracle_config()

    if not config.cdb_service:
        raise RuntimeError("Missing ORACLE_CDB_SERVICE.")

    service_name = normalize_service_name(config.cdb_service)

    return f"{config.host}:{config.port}/{service_name}"


def build_pdb_dsn(pdb_name: str | None = None) -> str:
    """
    Build DSN for a selected PDB.

    If pdb_name is None, use ORACLE_DEFAULT_PDB.
    If ORACLE_DSN is configured and no default PDB exists, use ORACLE_DSN.
    """
    db_debug(f"build_pdb_dsn called with pdb_name={pdb_name!r}")

    config = get_oracle_config()

    db_debug(
        "Oracle config loaded: "
        f"host={config.host!r}, "
        f"port={config.port!r}, "
        f"default_pdb={config.default_pdb!r}, "
        f"dsn_configured={bool(config.dsn)}"
    )

    service_name = pdb_name or config.default_pdb

    db_debug(f"Raw selected service_name={service_name!r}")

    if not service_name:
        if config.dsn:
            db_debug(f"No service_name found. Using configured ORACLE_DSN={config.dsn!r}")
            return config.dsn

        db_debug("No service_name and no ORACLE_DSN found. Raising error.")
        raise RuntimeError("Missing ORACLE_DEFAULT_PDB or ORACLE_DSN.")

    if service_name.upper() == "PDB$SEED":
        db_debug("Rejected PDB$SEED because it is read-only seed PDB.")
        raise RuntimeError("PDB$SEED is read-only and should not be used for normal PDB queries.")

    normalized_service_name = normalize_service_name(service_name)

    db_debug(f"Normalized service_name={normalized_service_name!r}")

    dsn = f"{config.host}:{config.port}/{normalized_service_name}"

    db_debug(f"Final PDB DSN={dsn!r}")

    return dsn


def get_oracle_user_password() -> tuple[str, str]:
    config = get_oracle_config()

    user = config.user
    password = get_secret("ORACLE_PASSWORD")

    missing = []

    if not user:
        missing.append("ORACLE_USER")

    if not password:
        missing.append("ORACLE_PASSWORD or ORACLE_PASSWORD_FILE")

    if missing:
        raise RuntimeError(f"Missing Oracle configuration: {', '.join(missing)}")

    return user, password


@contextmanager
def get_cdb_connection():
    """
    Connect to CDB/root.
    """
    user, password = get_oracle_user_password()
    dsn = build_cdb_dsn()

    conn = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn,
    )

    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_pdb_connection(pdb_name: str | None = None):
    """
    Connect to selected PDB.
    """
    user, password = get_oracle_user_password()
    dsn = build_pdb_dsn(pdb_name)

    conn = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn,
    )

    try:
        yield conn
    finally:
        conn.close()


def _rows_to_dicts(cursor, rows) -> list[dict]:
    columns = [col[0].lower() for col in cursor.description]
    result = [dict(zip(columns, row)) for row in rows]

    if result:
        return result

    return [
        {
            "message": "Query completed successfully but returned no rows.",
            "row_count": 0,
        }
    ]


def fetch_all_cdb(sql: str, binds: dict | None = None) -> list[dict]:
    """
    Run query against CDB/root.
    """
    with get_cdb_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, binds or {})
            rows = cur.fetchall()
            return _rows_to_dicts(cur, rows)


def fetch_all_pdb(
    sql: str,
    binds: dict | None = None,
    pdb_name: str | None = None,
) -> list[dict]:
    """
    Run query against selected PDB.
    """
    with get_pdb_connection(pdb_name=pdb_name) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, binds or {})
            rows = cur.fetchall()
            return _rows_to_dicts(cur, rows)


# Backward-compatible helper.
# Existing code that calls fetch_all(sql) will still work against the default PDB.
def fetch_all(
    sql: str,
    binds: dict | None = None,
    pdb_name: str | None = None,
) -> list[dict]:
    return fetch_all_pdb(sql=sql, binds=binds, pdb_name=pdb_name)
