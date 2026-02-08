import sqlite3
from typing import Tuple

from repo import COUPON_REPO_TYPE, COUPON_REPO_CONFIG

DB_PATH_CONF = "db_path"
TABLE_NAME_CONF = "table_name"




def initialize_db(db_name: str, table_name: str):
    """Initialize the database and create the coupons table."""
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create the coupons table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id TEXT PRIMARY KEY
                CHECK (length(id) = 20 AND id GLOB '[0-9]*'),  -- 20-digit numeric string
            denominal REAL NOT NULL,
            expiration_date DATE,
            created_at DATE,
            status TEXT NOT NULL CHECK (status IN ('AVAILABLE', 'RESERVED', 'USED')),
            bunch_id TEXT,
            processing_id TEXT,
            processing_date DATETIME
        );
    """)

    # Index to speed up finding available coupons by denominal and expiration
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_avail_denominal_exp
        ON coupons(denominal, expiration_date, created_at)
        WHERE status = 'AVAILABLE';
    """)


    # Index on finding coupons by bunch_id where status is RESERVED
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_bunch_id
        ON coupons(bunch_id)
        WHERE status = 'RESERVED';
    """)


    conn.commit()
    conn.close()
    print("Database and table initialized.")


def get_sqlite_credentials() -> Tuple[str,str]:
    """Get the SQLite database credentials from the configuration."""
    if COUPON_REPO_TYPE != "sqlite":
        raise ValueError(f"Expected COUPON_REPO_TYPE to be 'sqlite', but got {COUPON_REPO_TYPE}.")
    db_path = COUPON_REPO_CONFIG.get(DB_PATH_CONF)
    table_name = COUPON_REPO_CONFIG.get(TABLE_NAME_CONF)
    if not db_path or not table_name:
        raise ValueError("Database path and table name must be provided in COUPON_REPO_CONFIG.")
    return db_path, table_name


def main():
    db_path, table_name = get_sqlite_credentials()
    initialize_db(db_path, table_name)


if __name__ == "__main__":
    main()
