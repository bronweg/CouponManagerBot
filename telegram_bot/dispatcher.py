from typing import Set

from telegram.ext import ApplicationBuilder, Application

from app_service.coupon_provider import CouponProvider

from repo import COUPON_REPO_TYPE, COUPON_REPO_CONFIG
from repo.abstract_repo import AbstractCouponRepository


from telegram_bot.handler_factory import UsersAwareHandlerFactory
from telegram_bot.handlers import balance_command, json_command, pay_command, button_callback



def register_coupon_service(application: Application) -> None:
    """Register the coupon service with the application.
    Args:
        application (Application): The Telegram application instance.
    """
    coupon_provider = CouponProvider(AbstractCouponRepository.get_implementation(COUPON_REPO_TYPE)(COUPON_REPO_CONFIG))
    application.bot_data["coupon_provider"] = coupon_provider


def register_handlers(application, allowed_user_ids) -> None:
    """Register command and callback query handlers with the application.
    Args:
        application (Application): The Telegram application instance.
        allowed_user_ids (Set[int]): Set of user IDs allowed to use the bot.
    """
    handler_factory = UsersAwareHandlerFactory(allowed_user_ids)

    application.add_handler(handler_factory.get_command_handler("balance", balance_command))
    application.add_handler(handler_factory.get_command_handler("json", json_command))
    application.add_handler(handler_factory.get_command_handler("pay", pay_command))
    application.add_handler(handler_factory.get_callback_query_handler(button_callback))


def get_application(token: str, allowed_user_ids: Set[int]) -> Application:
    """Create and configure the Telegram application.
    Args:
        token (str): The bot token for the Telegram bot.
        allowed_user_ids (Set[int]): Set of user IDs allowed to use the bot.
    Returns:
        Application: The configured Telegram application instance.
    """
    application = ApplicationBuilder().token(token).build()
    register_coupon_service(application)
    register_handlers(application, allowed_user_ids)
    return application


