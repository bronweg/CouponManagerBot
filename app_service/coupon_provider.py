import logging
from io import BytesIO
from typing import Tuple, List

from barcoder.generator import generate_barcode
from combinator.core import get_coupons_combination
from repo.abstract_repo import AbstractCouponRepository
from repo.db_exceptions import CouponUnavailableError

logger = logging.getLogger(__name__)


class CouponProvider:
    def __init__(self, coupon_repo: AbstractCouponRepository):
        self.repo = coupon_repo

    def get_balance(self) -> List[Tuple[float, int]]:
        """ Returns a summary of available coupons grouped by denominal.
        Each tuple contains (denominal, amount).
        Returns:
            List of tuples where each tuple contains (denominal, amount).
        """
        return self.repo.get_available_summary()

    def get_coupons(self, amount_to_pay: int, bunch_id: str, more_tries: int = 3
                    ) -> Tuple[float, List[Tuple[str, BytesIO]]]:
        """ Returns a combination of cash to add and coupons to use for the given amount to pay.
        Args:
            amount_to_pay: The total amount to pay.
            bunch_id: The ID of the bunch to which the coupons will be assigned.
            more_tries: Number of retries if not enough coupons are available.
        Returns:
            A tuple containing:
                - cash_to_add: The amount of cash to add.
                - coupons_with_barcode: A list of tuples where each tuple contains (coupon_id, barcode image).
        Raises:
            CouponUnavailableError: If there are not enough coupons available after multiple attempts.
        """
        available_coupons = self.repo.get_available_summary()
        cash_to_add, coupons_to_use = get_coupons_combination(amount_to_pay, available_coupons)

        try:
            reserved_coupons = self.repo.reserve_coupons_by_bunch(coupons_to_use, bunch_id)
        except CouponUnavailableError as e:
            if more_tries > 0:
                logger.warning(f'Not enough coupons available, retrying {more_tries} more times.')
                reserved_coupons = self.get_coupons(amount_to_pay, bunch_id, more_tries - 1)
            else:
                logger.error(f'Not enough coupons available after multiple attempts. Giving up.')
                raise e

        try:
            coupons_with_barcode = [
                (coupon_id, generate_barcode(coupon_id, denominal)) for coupon_id, denominal in reserved_coupons
            ]
        except Exception as e:
            logger.error(f'Error generating barcodes for reserved coupons: {e}')
            try:
                self.repo.reject_coupons(bunch_id, ignore_processing_id=True)
            except Exception as reject_error:
                logger.error(f'Failed to reject coupons after barcode generation failure: {reject_error}')
            raise RuntimeError('Failed to generate barcodes for reserved coupons.', e)

        logger.debug(f'Cash to add: {cash_to_add}, Coupons reserved: {len(coupons_with_barcode)}')

        return cash_to_add, coupons_with_barcode

    def set_coupon_processing_id(self, coupon_code: str, processing_id: str) -> None:
        """ Sets the processing ID for a coupon.
        Args:
            coupon_code: The ID of the coupon to update.
            processing_id: The new processing ID to set.
        Raises:
            CouponUnavailableError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED or already has a processing ID.
        """
        self.repo.set_processing_id(coupon_code, processing_id)

    def use_coupon(self, coupon_code: str) -> str:
        """ Marks a coupon as used.
        Args:
            coupon_code: The ID of the coupon to mark as used.
        Returns:
            The processing ID of the coupon if it was reserved, otherwise None.
        Raises:
            CouponUnavailableError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED.
        """
        return self.repo.use_coupon(coupon_code)

    def reject_coupon(self, coupon_code: str) -> str:
        """ Rejects a coupon by changing its status to REJECTED.
        Args:
            coupon_code: The ID of the coupon to reject.
        Returns:
            The processing ID of the coupon if it was reserved.
        Raises:
            CouponUnavailableError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED.
        """
        return self.repo.reject_coupon(coupon_code)

    def use_coupons(self, bunch_id: str) -> List[str]:
        """ Marks all coupons in a bunch as used.
        Args:
            bunch_id: The ID of the bunch to mark as used.
        Returns:
            A list of processing IDs for the coupons that were marked as used.
        Raises:
            CouponUnavailableError: If the bunch does not exist or has no coupons.
            BadCouponStatusError: If any coupon's current status is not RESERVED.
        """
        return self.repo.use_coupons(bunch_id)

    def reject_coupons(self, bunch_id: str, ignore_processing_id: bool = False) -> List[str]:
        """ Rejects all coupons in a bunch by changing their status to REJECTED.
        Args:
            bunch_id: The ID of the bunch to reject.
            ignore_processing_id: If True, ignores the processing ID check and allows changing status even if processing ID is not set.
        Returns:
            A list of processing IDs for the coupons that were rejected.
        Raises:
            CouponUnavailableError: If the bunch does not exist or has no coupons.
            BadCouponStatusError: If any coupon's current status is not RESERVED.
        """
        return self.repo.reject_coupons(bunch_id, ignore_processing_id)

    def get_processing_ids_for_bunch(self, bunch_id: str) -> List[str]:
        """ Retrieves processing IDs for all coupons in a bunch.
        Args:
            bunch_id: The ID of the bunch to retrieve processing IDs for.
        Returns:
            A list of processing IDs for the coupons in the specified bunch.
        Raises:
            CouponUnavailableError: If the bunch does not exist or has no coupons.
        """
        return self.repo.get_processing_ids_for_bunch(bunch_id)

