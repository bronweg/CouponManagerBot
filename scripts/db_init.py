import sqlite3

DB_NAME = "../resources/coupon_management.db"
TABLE_NAME = "coupons"

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create the coupons table
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id TEXT PRIMARY KEY
                CHECK (length(id) = 20 AND id GLOB '[0-9]*'),  -- 20-digit numeric string
            denominal REAL NOT NULL,
            expiration_date DATE,
            status TEXT NOT NULL CHECK (status IN ('AVAILABLE', 'RESERVED', 'USED')),
            bunch_id TEXT,
            processing_id TEXT,
            processing_date DATETIME
        );
    """)

    # Index to speed up finding available coupons by denominal and expiration
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_coupons_avail_denominal_exp
        ON coupons(denominal, expiration_date)
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

if __name__ == "__main__":
    initialize_db()
