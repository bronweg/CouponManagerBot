import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class _CouponInPossession:
    denomination: float
    quantity: int


class _CouponsInPossession:

    @classmethod
    def from_denomination_amount_tuples(
            cls, denomination_amount_tuples: List[Tuple[float, int]], is_sorted = True
    ) -> '_CouponsInPossession':
        """
        Create a CouponsInPossession instance from a list of (denomination, quantity) tuples.

        Parameters:
            denomination_amount_tuples: A list of (denomination, quantity) pairs.
            is_sorted:
                - If True, assumes input is already sorted in ascending order by denomination
                  and contains no duplicates (recommended when loading from DB).
                - If False, input will be sorted and duplicate denominations will be merged automatically.

        Returns:
            CouponsInPossession object with internal normalized structure.
        """
        if not is_sorted:
            merged = defaultdict(int)
            for denomination, qty in denomination_amount_tuples:
                merged[denomination] += qty
            denomination_amount_tuples = sorted(merged.items())
        coupons = [_CouponInPossession(denomination, quantity) for denomination, quantity in denomination_amount_tuples]
        return cls(coupons)

    def __init__(self, coupons: List[_CouponInPossession]):
        self.__coupons = coupons

    def emit_max_denomination_used(self) -> Tuple[float, '_CouponsInPossession']:
        if not self.__coupons:
            raise RuntimeError('There are no coupons in possession to emit!')
        max_coupon = self.__coupons[-1]
        if max_coupon.quantity > 1:
            max_coupon_left = [_CouponInPossession(max_coupon.denomination, max_coupon.quantity - 1)]
        else:
            max_coupon_left = []
        return max_coupon.denomination, _CouponsInPossession(self.__coupons[:-1] + max_coupon_left)

    def emit_max_denomination_discarded(self) -> '_CouponsInPossession':
        if not self.__coupons:
            raise RuntimeError('There are no coupons in possession to discard!')
        return _CouponsInPossession(self.__coupons[:-1])

    def __bool__(self):
        return bool(self.__coupons)

    def __str__(self):
        return str(self.__coupons)



def choose_optimal(*usages: Optional[Tuple[float, List[float]]]) -> Tuple[float, List[float]]:
    real_usages = [usage for usage in usages if usage is not None]
    if not real_usages:
        raise RuntimeError('There is no possible coupons combination!!!')
    best_combination = min(real_usages,
                           key=lambda combination: (combination[0], len(combination[1])))
    return best_combination


def get_coupons_combination(
        cash_to_add: float, coupons_in_possession: List[Tuple[float, int]], coupons_used: List[float] = None
) -> Optional[Tuple[float, List[Tuple[float, int]]]]:
    coupons_combination_amount_and_list =  _get_coupons_combination(
        cash_to_add,
        _CouponsInPossession.from_denomination_amount_tuples(coupons_in_possession),
        coupons_used
    )
    if coupons_combination_amount_and_list is None:
        raise RuntimeError(
            "Something went wrong, when trying to find coupons combination "
            f"for {cash_to_add} with {coupons_in_possession}!")

    cash_to_add, coupons_used = coupons_combination_amount_and_list
    coupons_used_dict = defaultdict(int)
    for coupon in coupons_used:
        coupons_used_dict[coupon] += 1
    return cash_to_add, list(coupons_used_dict.items())



def _get_coupons_combination(
        cash_to_add: float, coupons_in_possession: _CouponsInPossession, coupons_used: List[float] = None
) -> Optional[Tuple[float, List[float]]]:

    logger.debug(coupons_in_possession)

    if coupons_used is None:
        coupons_used = []

    if cash_to_add < 0:
        return  None

    current_combination = (cash_to_add, coupons_used)
    if cash_to_add == 0 or not coupons_in_possession:
        return current_combination


    max_denomination_amount, use_max_left_coupons = coupons_in_possession.emit_max_denomination_used()
    more_of_same_denomination_combination = _get_coupons_combination(
        cash_to_add - max_denomination_amount,
        use_max_left_coupons,
        coupons_used + [max_denomination_amount]
    )

    skip_max_left_coupons = coupons_in_possession.emit_max_denomination_discarded()
    skip_to_next_denomination_combination = _get_coupons_combination(
        cash_to_add,
        skip_max_left_coupons,
        coupons_used
    )

    return choose_optimal(
        current_combination,
        more_of_same_denomination_combination,
        skip_to_next_denomination_combination
    )


if __name__ == '__main__':
    # available_coupons = [
    #     (5.0, 2),
    #     (10.0, 3),
    #     (15.0, 2),
    # ]

    # available_coupons = [(5.0, 18), (10.0, 17), (15.0, 25), (20.0, 17)]

    available_coupons = [(15.0, 25), (20.0, 17)]

    amount_to_pay = 35
    pay_with_this = get_coupons_combination(amount_to_pay, available_coupons)
    print(pay_with_this)