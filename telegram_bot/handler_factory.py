"""Factory for creating Telegram bot handlers that are aware of users filtering."""
import logging
from typing import Collection, Callable, Coroutine, Any

from telegram import Update
from telegram.ext import CommandHandler, CallbackQueryHandler, filters, ContextTypes

Callback = Callable[[Update, ContextTypes.DEFAULT_TYPE], Coroutine[Any, Any, None]]

logger = logging.getLogger(__name__)

class UsersAwareHandlerFactory:
    """Factory for creating command and callback query handlers that are aware of specific users.
    This factory allows you to create handlers that will only respond to updates from specified users.
    It uses a user filter to restrict access to the handlers based on user IDs.
    Args:
        users (Collection[int]): A collection of user IDs that the handlers should respond to.
    """

    def __init__(self, users: Collection[int]):
        self.user_filter = self._create_filter(users)

    @staticmethod
    def _create_filter(users: Collection[int]) -> filters.User:
        """Creates a user filter based on the provided user IDs.
        Args:
            users (Collection[int]): A collection of user IDs.
        Returns:
            filters.User: A user filter that restricts access to the specified user IDs.
        """
        return filters.User(user_id=users) if users else None


    def get_command_handler(self, command: str, callback: Callback) -> CommandHandler:
        """Creates a command handler that responds to a specific command and is filtered by user IDs.
        Args:
            command (str): The command that the handler should respond to.
            callback (Callback): The callback function to be executed when the command is received.
        Returns:
            CommandHandler: A command handler that responds to the specified command and is filtered by user IDs.
        """
        return CommandHandler(command, callback, filters=self.user_filter)


    def get_callback_query_handler(self, callback: Callback) -> CallbackQueryHandler:
        """Creates a callback query handler that responds to callback queries and is filtered by user IDs.
        Args:
            callback (Callback): The callback function to be executed when a callback query is received.
        Returns:
            CallbackQueryHandler: A callback query handler that responds to callback queries and is filtered by user IDs.
        """
        if not self.user_filter:
            return CallbackQueryHandler(callback)

        async def filtered_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
            if not update.effective_user.id in self.user_filter.user_ids:
                await update.callback_query.answer()
                return
            await callback(update, context)

        return CallbackQueryHandler(filtered_callback)