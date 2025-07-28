import sqlite3
import string
from datetime import datetime, timedelta
import random

from scripts.sqlite_db_init import get_sqlite_credentials

DB_NAME, TABLE_NAME = get_sqlite_credentials()


def generate_coupon_id():
    # Generates a 20-digit random numeric string
    return ''.join(random.choices(string.digits, k=20))

def generate_processing_id():
    # Generates a 20-digit random numeric string
    return ''.join(random.choices(string.octdigits, k=5))

def populate_coupons_in_action(n=100):
    statuses = ['AVAILABLE', 'RESERVED', 'USED']
    denominals = [5.0, 10.0, 15.0, 20.0]
    bunch_ids = ['BUNCH_A', 'BUNCH_B']

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.today()

    for i in range(n):
        coupon_id = generate_coupon_id()
        denominal = random.choice(denominals)
        status = random.choices(statuses, weights=[0.5, 0.3, 0.2])[0]
        expiration_date_random = (today + timedelta(days=random.randint(-10, 60))).date().isoformat()
        expiration_date = random.choices([expiration_date_random, None], weights=[0.6, 0.4])[0]
        bunch_id = random.choice(bunch_ids if status == 'RESERVED' else [None])
        processing_id = generate_processing_id() if status == 'RESERVED' else None

        cursor.execute(f"""
            INSERT INTO {TABLE_NAME} (id, denominal, expiration_date, status, bunch_id, processing_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (coupon_id, denominal, expiration_date, status, bunch_id, processing_id))

    conn.commit()
    conn.close()
    print(f"Inserted {n} test coupons.")

def populate_coupons_from_scratch(n=100):
    denominals = [5.0, 10.0, 15.0, 20.0]

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.today()

    for i in range(n):
        coupon_id = generate_coupon_id()
        denominal = random.choice(denominals)
        status = 'AVAILABLE'
        expiration_date_random = (today + timedelta(days=random.randint(-10, 60))).date().isoformat()
        expiration_date = random.choices([expiration_date_random, None], weights=[0.6, 0.4])[0]

        cursor.execute(f"""
                INSERT INTO {TABLE_NAME} (id, denominal, expiration_date, status)
                VALUES (?, ?, ?, ?)
            """, (coupon_id, denominal, expiration_date, status))

    conn.commit()
    conn.close()
    print(f"Inserted {n} fresh test coupons.")



if __name__ == "__main__":
    populate_coupons_from_scratch()
