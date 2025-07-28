import json
from typing import Dict, List

from repo import COUPON_REPO_TYPE, COUPON_REPO_CONFIG
from repo.abstract_repo import AbstractCouponRepository



JSON_FILE = '../resources/coupons.json'


def load_from_json() -> Dict[str, List[str]]:
    """Load coupons from a JSON file."""
    with open(JSON_FILE, 'r') as file:
        coupons = json.load(file)
    return coupons

def insert_coupons_to_db(coupons: Dict[str, List[str]]):
    """Insert coupons into the database."""
    coupon_repo = AbstractCouponRepository.get_implementation(COUPON_REPO_TYPE)(COUPON_REPO_CONFIG)
    coupon_repo.insert_eternal_coupons(coupons)


def main():
    coupons = load_from_json()
    insert_coupons_to_db(coupons)



if __name__ == "__main__":
    main()


