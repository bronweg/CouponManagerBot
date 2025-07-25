
class CouponUnavailableError(Exception):
    """Raised when the requested coupons are not available."""
    pass

class NonExistingCouponError(Exception):
    """Raised when a coupon with None ID is requested."""
    pass

class BadCouponStatusError(Exception):
    """Raised when the coupon has an unexpected status."""
    pass