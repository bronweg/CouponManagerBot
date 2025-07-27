import json
import sqlite3
from typing import Dict, List

from scripts.db_init import DB_NAME, TABLE_NAME

JSON_FILE = '../resources/coupons.json'


def load_from_json() -> Dict[str, List[str]]:
    """Load coupons from a JSON file."""
    with open(JSON_FILE, 'r') as file:
        coupons = json.load(file)
    return coupons

def insert_coupons_to_db(coupons: Dict[str, List[str]]):
    """Insert coupons into the database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    coupon_counter = 0
    try:
        for denominal, coupon_list in coupons.items():
            for coupon_id in coupon_list:
                cursor.execute(f"""
                    INSERT INTO {TABLE_NAME} (id, denominal, expiration_date, status)
                    VALUES (?, ?, ?, ?)
                """, (coupon_id, float(denominal), None, 'AVAILABLE'))
                coupon_counter += 1
        conn.commit()
        print(f"All done! {coupon_counter} coupons inserted into the database.")
    except Exception as e:
        print(f"An error occurred while inserting coupons: {e}")
        conn.rollback()
    finally:
        cursor.close()

    conn.close()


def main():
    coupons = load_from_json()
    insert_coupons_to_db(coupons)


def not_main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {TABLE_NAME}")
    rows = cursor.fetchall()
    for row in rows:
        print(row)


if __name__ == "__main__":
    # main()
    not_main()

