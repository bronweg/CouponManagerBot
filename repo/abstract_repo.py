from abc import ABC, abstractmethod
from typing import List, Tuple, Dict

from enum import Enum, auto



class CouponStatus(Enum):
    AVAILABLE = auto()
    RESERVED = auto()
    USED = auto()


class AbstractCouponRepository(ABC):

    conf_name = ''
    __implementations: Dict[str, type['AbstractCouponRepository']] = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        conf_name = cls.conf_name if cls.conf_name else cls.__name__
        AbstractCouponRepository.__implementations[conf_name] = cls

    @classmethod
    def get_implementation(cls, config_str: str) -> type['AbstractCouponRepository']:
        """ Get a registered implementation of the AbstractCouponRepository by its config string. """
        if config_str not in cls.__implementations:
            raise ValueError(f"No implementation registered for {config_str}.\nCurrently available: {list(cls.__implementations.keys())}")
        return cls.__implementations[config_str]


    def __init__(self, config: Dict[str, str] = None):
        """ Initialize the repository. This method should be overridden by subclasses to set up the database or other storage. """
        pass

    @abstractmethod
    def get_available_summary(self) -> List[Tuple[float, int]]:
        """ Returns a summary of available coupons grouped by denominal.
        Each tuple contains (denominal, amount).
        Returns:
            List of tuples where each tuple contains (denominal, amount).
        """
        ... # pragma: no cover

    @abstractmethod
    def insert_eternal_coupons(self, coupons_json: Dict[str, Dict[str, List[str]]]) -> int:
        """ Inserts coupons into the repository.
        Args:
            coupons_json: A dictionary where keys are denominals and values are lists of coupon IDs.
        Returns:
            The number of coupons successfully inserted.
        Raises:
            ValueError: If the input format is incorrect or if any coupon ID is invalid.
        """
        ... # pragma: no cover

    @abstractmethod
    def reserve_coupons_by_bunch(self, denominal_requirements: List[Tuple[float, int]], bunch_id: str) \
            -> List[Tuple[str, float]]:
        """ Reserve coupons based on the provided denominal requirements and assign them to a bunch_id.
        Args:
            denominal_requirements: List of tuples where each tuple contains (denominal, amount).
            bunch_id: The ID to assign to the reserved coupons.
        Returns:
            List of tuples (coupon_id, denominal) for the coupons that were successfully reserved.
        Raises:
            CouponUnavailableError: If there are not enough AVAILABLE coupons for a given denominal.
        """
        ... # pragma: no cover

    @abstractmethod
    def set_processing_id(self, coupon_code: str, processing_id: str) -> None:
        """ Sets the processing_id for a coupon.
        Args:
            coupon_code: The ID of the coupon to update.
            processing_id: The new processing_id to set.
        Raises:
            NonExistingCouponError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED or coupon already has a processing_id.
        """
        ... # pragma: no cover

    @abstractmethod
    def apply_reject_coupon(
            self, coupon_code, new_status: CouponStatus, keep_info: bool, ignore_processing_id: bool = False
    ) -> str:
        """ Applies a new status to a coupon and optionally keeps its processing information.
        Args:
            coupon_code: The ID of the coupon to update.
            new_status: The new status to apply to the coupon.
            keep_info: If True, keeps processing information (processing_id, processing_date).
                       If False, clears processing information.
            ignore_processing_id: If True, ignores the processing_id check and allows changing status even if processing_id is not set.
        Returns:
            The processing_id of the coupon if it was reserved, otherwise None.
        Raises:
            NonExistingCouponError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED.
        """
        ... # pragma: no cover

    def use_coupon(self, coupon_code) -> str:
        """ Uses a coupon by changing its status to USED.
        Args:
            coupon_code: The ID of the coupon to use.
        Returns:
            The processing_id of the coupon if it was reserved.
        Raises:
            NonExistingCouponError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED.
        """
        return self.apply_reject_coupon(coupon_code, CouponStatus.USED, keep_info=True)

    def reject_coupon(self, coupon_code, ignore_processing_id: bool = False) -> str:
        """ Rejects a coupon by changing its status to AVAILABLE.
        Args:
            coupon_code: The ID of the coupon to reject.
            ignore_processing_id: If True, ignores the processing_id check and allows changing status even if processing_id is not set.
        Returns:
            The processing_id of the coupon if it was reserved.
        Raises:
            NonExistingCouponError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED.
        """
        return self.apply_reject_coupon(
            coupon_code, CouponStatus.AVAILABLE, keep_info=False, ignore_processing_id=ignore_processing_id)

    @abstractmethod
    def apply_reject_coupons(
            self, bunch_id: str, status: CouponStatus, keep_info: bool, ignore_processing_id: bool = False
    ) -> List[str]:
        """ Applies a new status to all coupons in a bunch and optionally keeps their processing information.
        Args:
            bunch_id: The ID of the bunch to update.
            status: The new status to apply to the coupons.
            keep_info: If True, keeps processing information (processing_id, processing_date).
                       If False, clears processing information.
            ignore_processing_id: If True, ignores the processing_id check and allows changing status even if processing_id is not set.
        Returns:
            List of processing_ids of the coupons that were reserved.
        Raises:
            BadCouponStatusError: If any coupon in the bunch has a status other than RESERVED or processing_id is None.
        """
        ... # pragma: no cover

    def use_coupons(self, bunch_id: str) -> List[str]:
        """ Uses all coupons in a bunch by changing their status to USED.
        Args:
            bunch_id: The ID of the bunch to update.
        Returns:
            List of processing_ids of the coupons that were reserved for the given bunch and not applied/rejected yet.
        Raises:
            BadCouponStatusError: If any coupon in the bunch has a status other than RESERVED or processing_id is None.
        """
        return self.apply_reject_coupons(bunch_id, CouponStatus.USED, True)

    def reject_coupons(self, bunch_id: str, ignore_processing_id: bool = False) -> List[str]:
        """ Rejects all coupons in a bunch by changing their status to AVAILABLE.
        Args:
            bunch_id: The ID of the bunch to update.
            ignore_processing_id: If True, ignores the processing_id check and allows changing status even if processing_id is not set.
        Returns:
            List of processing_ids of the coupons that were reserved for the given bunch and not applied/rejected yet.
        Raises:
            BadCouponStatusError: If any coupon in the bunch has a status other than RESERVED or processing_id is None.
        """
        return self.apply_reject_coupons(
            bunch_id, CouponStatus.AVAILABLE, keep_info=False, ignore_processing_id=ignore_processing_id)

    @abstractmethod
    def get_processing_ids_for_bunch(self, bunch_id: str) -> List[str]:
        """ Retrieves processing_ids of all coupons in a bunch.
        Args:
            bunch_id: The ID of the bunch that were reserved for the given bunch and not applied/rejected yet.
        Returns:
            List of processing_ids of the coupons in the specified bunch.
        """
        ... # pragma: no cover

    @abstractmethod
    def sanity_long_processing(self) -> bool:
        """ Checks if there are any coupons with processing_id that have been in processing for more than 1 day.
        Returns:
            True if no long processing found, False otherwise.
        """
        ... # pragma: no cover

    @abstractmethod
    def sanity_status(self) -> bool:
        """ Checks if there are any coupons with processing data, while not reserved or used.

        Returns:
            True if no coupons with bad status found, False otherwise.
        """
        ... # pragma: no cover

    @abstractmethod
    def sanity_unknown_processing(self) -> bool:
        """ Checks if there are coupons have been processing for more than 5 minutes, but still have no processing_id.
        Returns:
            True if no coupons with no processing_id found, False otherwise.
        """
        ... # pragma: no cover

    @abstractmethod
    def alert_expiration(self) -> List[Tuple[str, str]]:
        """ Checks for coupons that are about to expire within the next 7 days.
        Returns:
            List of tuples (coupon_id, expiration_date), sorted by expiration_date in ascending order.
        """
        ... # pragma: no cover


