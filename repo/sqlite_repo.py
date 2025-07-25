import atexit
import logging
import sqlite3
from typing import List, Tuple

from repo.abstract_repo import AbstractCouponRepository, CouponStatus
from repo.db_exceptions import CouponUnavailableError, BadCouponStatusError, NonExistingCouponError

DB_PATH_CONF = "db_path"
TABLE_NAME_CONF = "table_name"

logger = logging.getLogger(__name__)


class SQLiteCouponRepository(AbstractCouponRepository):
    """SQLite implementation of the AbstractCouponRepository for managing coupons in a SQLite database."""

    conf_name = "sqlite"

    def __init__(self, config: dict = None):
        """Initialize the SQLiteCouponRepository and open a database connection."""
        super().__init__(config)
        self.db_path = config.get(DB_PATH_CONF)
        self.table_name = config.get(TABLE_NAME_CONF)
        self._db_connection = self.__open()
        atexit.register(self.__close)

    def __open(self) -> sqlite3.Connection:
        """Open the database connection."""
        return sqlite3.connect(self.db_path)

    def __close(self):
        """Close the database connection."""
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None


    def get_available_summary(self) -> List[Tuple[float, int]]:
        """ Returns a summary of available coupons grouped by denominal.
        Returns:
            List of tuples where each tuple contains (denominal, amount).
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("""
                SELECT denominal, COUNT(*) as amount
                FROM ?
                WHERE status = ?
                    AND (expiration_date >= date('now') OR expiration_date IS NULL)
                GROUP BY denominal
                ORDER BY denominal ASC;
            """, (self.table_name, CouponStatus.AVAILABLE.name,))
            return cursor.fetchall()
        finally:
            cursor.close()


    def reserve_coupons_by_bunch(self, denominal_requirements: List[Tuple[float, int]], bunch_id: str
                                 ) -> List[Tuple[str, float]]:
        """ Reserve coupons based on the provided denominal requirements and assign them to a bunch_id.
        Args:
            denominal_requirements: List of tuples where each tuple contains (denominal, amount).
            bunch_id: The ID to assign to the reserved coupons.
        Returns:
            List of tuples (coupon_id, denominal) for the coupons that were successfully reserved.
        Raises:
            CouponUnavailableError: If there are not enough AVAILABLE coupons for a given denominal.
        """
        cursor = self._db_connection.cursor()
        try:
            all_reserved = []
            cursor.execute("BEGIN IMMEDIATE")
            for denominal, amount in denominal_requirements:
                cursor.execute("""
                    SELECT id, denominal 
                    FROM ?
                    WHERE status = ?
                        AND (expiration_date >= date('now') OR expiration_date IS NULL)
                        AND denominal = ?
                    ORDER BY expiration_date ASC NULLS LAST
                    LIMIT ?
                """, (self.table_name, CouponStatus.AVAILABLE.name, denominal, amount))

                rows = cursor.fetchall()

                if len(rows) < amount:
                    raise CouponUnavailableError(f"Not enough AVAILABLE coupons for denominal {denominal}")

                all_reserved.extend(rows)

                cursor.executemany("""
                    UPDATE ?
                    SET status = ?, bunch_id = ?, processing_date = datetime('now')
                    WHERE id = ?
                """, [(self.table_name, CouponStatus.RESERVED.name, bunch_id, id_denominal[0]) for id_denominal in rows])

            self._db_connection.commit()
            logger.debug(f"Reserved coupons: {all_reserved}")
            return all_reserved

        except Exception as e:
            self._db_connection.rollback()
            if isinstance(e, CouponUnavailableError):
                logger.warning(f"These coupons already aren't available: {e}")
            else:
                logger.error(f"Transaction failed: {e}")
            raise e
        finally:
            cursor.close()


    def set_processing_id(self, coupon_code: str, processing_id: str) -> None:
        """ Sets the processing_id for a coupon.
        Args:
            coupon_code: The ID of the coupon to update.
            processing_id: The new processing_id to set.
        Raises:
            NonExistingCouponError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED or coupon already has a processing_id.
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute("""
                SELECT status, processing_id 
                FROM ?
                WHERE id = ?
            """, (self.table_name, coupon_code,))

            row = cursor.fetchone()
            if not row:
                raise NonExistingCouponError(f"Coupon {coupon_code} does not exist.")

            coupon_status, existing_processing_id = row

            if coupon_status != CouponStatus.RESERVED.name or existing_processing_id is not None:
                raise BadCouponStatusError(
                    f"Processing ID can not be set for coupon {coupon_code}. "
                    f"Current coupon status: {coupon_status}, processing_id: {existing_processing_id}"
                )

            cursor.execute("""
                UPDATE ?
                SET processing_id = ?
                WHERE id = ?
            """, (self.table_name, processing_id, coupon_code))

            self._db_connection.commit()
        except Exception as e:
            self._db_connection.rollback()
            logger.error(f"Failed to set processing_id for coupon {coupon_code}: {e}")
            raise e
        finally:
            cursor.close()


    def apply_reject_coupon(
            self, coupon_code, new_status: CouponStatus, keep_info: bool, ignore_processing_id: bool = False
    ) -> str:
        """ Updates a coupon's status and optionally keeps its processing information.
        Args:
            coupon_code: The ID of the coupon to update.
            new_status: The new status to apply to the coupon.
            keep_info: If True, keeps processing information (processing_id, processing_date).
                       If False, clears processing information.
            ignore_processing_id: If True, ignores the processing_id check and allows changing status even if processing_id is not set.
        Returns:
            The processing_id of the coupon.
        Raises:
            NonExistingCouponError: If the coupon does not exist.
            BadCouponStatusError: If the coupon's current status is not RESERVED.
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute("""
                SELECT status, processing_id 
                FROM ?
                WHERE id = ?
            """, (self.table_name, coupon_code,))

            row = cursor.fetchone()
            if not row:
                raise NonExistingCouponError(f"Coupon {coupon_code} does not exist.")

            coupon_status, processing_id = row

            if coupon_status != CouponStatus.RESERVED.name:
                raise BadCouponStatusError(f"Coupon {coupon_code} status can not be changed to {new_status.name}. "
                                             f"Current status: {coupon_status}")

            if processing_id is None:
                if not ignore_processing_id:
                    raise BadCouponStatusError(f"Coupon {coupon_code} has no processing_id set. "
                                               f"Current status: {coupon_status}")
                else:
                    logger.warning(f"Coupon {coupon_code} has no processing_id set, still processing status change.")

            if keep_info:
                cursor.execute("""
                    UPDATE ?
                    SET status = ?, bunch_id = NULL
                    WHERE id = ?
                """, (self.table_name, new_status.name, coupon_code))
            else:
                cursor.execute("""
                    UPDATE ?
                    SET status = ?, bunch_id = NULL, processing_id = NULL, processing_date = NULL
                    WHERE id = ?
                """, (self.table_name, new_status.name, coupon_code))

            self._db_connection.commit()
            return processing_id
        except Exception as e:
            self._db_connection.rollback()
            logger.error(f"Failed to apply status {new_status.name} to coupon {coupon_code}: {e}")
            raise e
        finally:
            cursor.close()


    def apply_reject_coupons(
            self, bunch_id: str, status: CouponStatus, keep_info: bool, ignore_processing_id: bool = False) -> List[str]:
        """ Applies a new status to all coupons in a bunch and optionally keeps their processing information.
        Args:
            bunch_id: The ID of the bunch to update.
            status: The new status to apply to the coupons.
            keep_info: If True, keeps processing information (processing_id, processing_date).
                       If False, clears processing information.
            ignore_processing_id: If True, ignores the processing_id check and allows changing status even if processing_id is not set.
        Returns:
            List of processing_ids of the coupons that were reserved for the given bunch and not applied/rejected yet.
        Raises:
            BadCouponStatusError: If any coupon in the bunch has a status other than RESERVED or processing_id is None.
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("BEGIN IMMEDIATE")

            cursor.execute("""
                SELECT id, status, processing_id 
                FROM ?
                WHERE bunch_id = ?
            """, (self.table_name, bunch_id))
            rows = cursor.fetchall()

            id_idx = 0
            status_idx = 1
            processing_idx = 2


            if not ignore_processing_id:
                bad_statuses = [
                    {'coupon_id': row[id_idx], 'status': row[status_idx], 'processing_id' : row[processing_idx]}
                    for row in rows if row[status_idx] != CouponStatus.RESERVED.name or row[processing_idx] is None
                ]
            else:
                bad_statuses = [
                    {'coupon_id': row[id_idx], 'status': row[status_idx]}
                    for row in rows if row[status_idx] not in [CouponStatus.RESERVED.name, CouponStatus.USED.name]
                ]
                bad_processing_ids = [
                    {'coupon_id': row[id_idx], 'status': row[status_idx]}
                    for row in rows if  row[processing_idx] is None
                ]
                if bad_processing_ids:
                    logger.warning(
                        f"Coupons missing processing_id found: {bad_processing_ids}, still processing status change."
                    )

            if bad_statuses:
                raise BadCouponStatusError(f"Coupons with bunch_id {bunch_id} have bad status: {bad_statuses}")

            if keep_info:
                cursor.execute("""
                    UPDATE ?
                    SET status = ?, bunch_id = NULL
                    WHERE bunch_id = ?
                """, (self.table_name, status.name, bunch_id,))
            else:
                cursor.execute("""
                    UPDATE ?
                    SET status = ?, bunch_id = NULL, processing_id = NULL, processing_date = NULL
                    WHERE bunch_id = ?
                """, (self.table_name, status.name, bunch_id,))

            self._db_connection.commit()
            return [coupon_in_bunch[processing_idx] for coupon_in_bunch in rows]
        except Exception as e:
            self._db_connection.rollback()
            logger.error(f"Failed to apply status {status.name} to bunch {bunch_id}: {e}")
            raise e
        finally:
            cursor.close()


    def get_processing_ids_for_bunch(self, bunch_id: str) -> List[str]:
        """ Retrieves processing_ids of all coupons in a bunch.
        Args:
            bunch_id: The ID of the bunch to query.
        Returns:
            List of processing_ids of the coupons that were reserved for the given bunch and not applied/rejected yet.
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("""
                SELECT processing_id 
                FROM ?
                WHERE bunch_id = ?
            """, (self.table_name, bunch_id))

            processing_ids = cursor.fetchall()
            return [pid[0] for pid in processing_ids]
        finally:
            cursor.close()


    def sanity_long_processing(self) -> bool:
        """ Checks if there are any coupons with processing_id that have been in processing for more than 1 day.
        Returns:
            True if no long processing found, False otherwise.
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("""
                SELECT id 
                FROM ?
                WHERE processing_id IS NOT NULL
                    AND status = ?
                    AND processing_date < datetime('now', '-1 day')
            """, (self.table_name, CouponStatus.RESERVED.name))

            long_processing = cursor.fetchall()
            if long_processing:
                logger.warning(f"Coupons with long processing found: {long_processing}")
                return False
            logger.info("No coupons with long processing found.")
            return True

        finally:
            cursor.close()

    def sanity_status(self) -> bool:
        """ Checks if there are any coupons with processing data, while not reserved or used.
        Returns:
            True if no coupons with bad status found, False otherwise.
        """
        cursor = self._db_connection.cursor()

        try:
            cursor.execute("""
                SELECT id, status, bunch_id
                FROM ?
                WHERE status != ?
                AND (bunch_id IS NOT NULL)
            """, (self.table_name, CouponStatus.RESERVED.name))
            bad_bunch_status = cursor.fetchall()

            cursor.execute("""
                SELECT id, status, processing_id, processing_date
                FROM ?
                WHERE status NOT IN (?, ?)
                AND (processing_id IS NOT NULL OR processing_date IS NOT NULL)
            """, (self.table_name, CouponStatus.RESERVED.name, CouponStatus.USED.name))
            bad_processing_status = cursor.fetchall()

            if bad_bunch_status or bad_processing_status:
                if bad_bunch_status:
                    logger.warning(f"Coupons with bad bunch status found: {bad_bunch_status}")
                if bad_processing_status:
                    logger.warning(f"Coupons with bad processing status found: {bad_processing_status}")
                return False

            logger.info("No coupons with processing data stuck.")
            return True

        finally:
            cursor.close()

    def sanity_unknown_processing(self) -> bool:
        """ Checks if there are coupons have been processing for more than 5 minutes, but still have no processing_id.
        Returns:
            True if no coupons with no processing_id found, False otherwise.
        """
        cursor = self._db_connection.cursor()

        try:
            cursor.execute("""
                SELECT id 
                FROM ?
                WHERE status = ?
                    AND processing_date < datetime('now', '-5 minutes')
                    AND processing_id IS NULL           
            """, (self.table_name, CouponStatus.RESERVED.name))

            long_pre_processing = cursor.fetchall()
            if long_pre_processing:
                logger.warning(f"Coupons with unknown found: {long_pre_processing}")
                return False
            logger.info("No coupons with unknown found.")
            return True

        finally:
            cursor.close()

    def alert_expiration(self) -> List[Tuple[str, str]]:
        """ Checks for coupons that are about to expire within the next 7 days.
        Returns:
            List of tuples (coupon_id, expiration_date), sorted by expiration_date in ascending order.
        """
        cursor = self._db_connection.cursor()
        try:
            cursor.execute("""
                SELECT id, expiration_date 
                FROM ?
                WHERE expiration_date IS NOT NULL
                    AND expiration_date <= date('now', '+7 days')
                    AND status = ?
            """, (self.table_name, CouponStatus.AVAILABLE.name))

            return cursor.fetchall()
        finally:
            cursor.close()


if __name__ == "__main__":
    repo = SQLiteCouponRepository()
    print(repo.get_available_summary())



    print(repo.reserve_coupons_by_bunch([(15.0, 2), (5.0, 1)], "BUNCH_B"))

    # print(repo.sanity_unknown_processing())
    # print(repo.sanity_long_processing())
    # print(repo.alert_expiration())
    # print(repo.sanity_status())


    # print(repo.reserve_coupons_by_bunch([(20.0, 2), (10.0, 1)], "BUNCH_C"))
    # print(repo.get_available_summary())
    # print(repo.reject_coupon("33044816766138462041"))
    # print(repo.get_available_summary())


    # print(repo.reject_coupon("71565719369792755570"))
    # print(repo.use_coupon("84164051850976384485"))

    # print(repo.use_coupons("BUNCH_A"))

    # db_connection = repo._db_connection
    # main_cursor = db_connection.cursor()
    # try:
    #
    #     main_cursor.executemany("""
    #         UPDATE ?
    #         SET processing_id = ?
    #         WHERE id = ?
    #     """, [
    #         (repo.table_name, '03364', '40622267576381828942'), (repo.table_name, '13504', '71565316757713559100'),
    #         (repo.table_name, '22850', '25824193964951355004'), (repo.table_name, '55057', '71565719369792755570'),
    #         (repo.table_name, '29812', '47645142442778242859'), (repo.table_name, '75737', '07078752209623024234'),
    #         (repo.table_name, '40317', '84164051850976384485'), (repo.table_name, '27806', '70268469832712262468')
    #     ])
    #     db_connection.commit()
    # finally:
    #     main_cursor.close()


