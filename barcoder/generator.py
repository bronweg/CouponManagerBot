import logging

from io import BytesIO

import barcode
from barcode.writer import ImageWriter

logger = logging.getLogger(__name__)


def generate_barcode(coupon_id: str, amount: float) -> BytesIO:
    """
    Generate a barcoder image for a given coupon ID.

    Args:
      coupon_id: A 20-digit coupon ID string

    Returns:
      BytesIO object containing barcoder image data
      :param coupon_id:
      :param amount:
    """
    barcode_data = BytesIO()
    barcode_class = barcode.get_barcode_class('code128')
    barcode_instance = barcode_class(coupon_id, writer=ImageWriter())
    barcode_instance.write(
        barcode_data,
        text = f'{coupon_id} | ₪{amount}',
        options = {
            'font_size': 5,
            'text_distance': 2,
        }

    )
    barcode_data.seek(0)

    logger.debug(f"Generated barcoder image for coupon ID {coupon_id}")
    return barcode_data