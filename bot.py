#!/usr/bin/env python3
"""
Minimal Telegram Bot using python-telegram-bot library.

This bot responds to the /pay command with "pong".
The main application runs synchronously, but handlers use async for compatibility.
"""

import os
import logging
import asyncio
from functools import wraps
from typing import Set
from dataclasses import dataclass
from io import BytesIO
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import RetryAfter
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, \
    ContextTypes
from dotenv import load_dotenv
import barcode
from barcode.writer import ImageWriter

# Load environment variables from .env.local file
load_dotenv('.env.local')

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global dictionary to track message states
# Format: {message_id: {"multiplier": int, "status": "unprocessed"|"accepted"|"declined", "result": str}}
MESSAGE_STATES = {}


@dataclass
class BotConfig:
    """Centralized configuration for the bot."""
    bot_token: str
    allowed_user_ids: Set[int]

    @classmethod
    def from_environment(cls) -> 'BotConfig':
        """
        Load configuration from environment variables.

        Returns:
            BotConfig instance with loaded configuration

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        # Load bot token
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set!")

        # Load allowed user IDs
        allowed_users_str = os.getenv('ALLOWED_USER_IDS', '')
        logger.info(f"Raw allowed users config: {allowed_users_str}")

        if not allowed_users_str or allowed_users_str == 'your_user_id_here':
            logger.warning("No allowed user IDs configured! Bot will reject all users.")
            allowed_user_ids = set()
        else:
            try:
                # Parse comma-separated user IDs
                allowed_user_ids = {int(uid.strip()) for uid in allowed_users_str.split(',') if uid.strip()}
                logger.info(f"Loaded {len(allowed_user_ids)} allowed user IDs")
            except ValueError as e:
                logger.error(f"Error parsing ALLOWED_USER_IDS: {e}")
                raise ValueError(f"Invalid ALLOWED_USER_IDS format: {e}")

        return cls(
            bot_token=bot_token,
            allowed_user_ids=allowed_user_ids
        )


def require_authorization(func):
    """
    Decorator to check if user is authorized before executing command.

    Args:
        func: The command handler function to wrap

    Returns:
        Wrapped function with authorization check
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"

        # Get bot config from application context
        bot_config: BotConfig = context.application.bot_data.get('config')

        if user_id not in bot_config.allowed_user_ids:
            logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
            # Handle both regular messages and callback queries
            if update.message:
                await update.message.reply_text("❌ Sorry, you are not authorized to use this bot.")
            elif update.callback_query:
                await update.callback_query.answer("❌ Sorry, you are not authorized to use this bot.")
            return None

        logger.info(f"Authorized user {user_id} (@{username}) executing command")
        return await func(update, context)

    return wrapper


def generate_barcode(coupon_id: str, amount: int) -> BytesIO:
    """
    Generate a barcode image for a given coupon ID.

    Args:
      coupon_id: A 20-digit coupon ID string

    Returns:
      BytesIO object containing barcode image data
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

    logger.info(f"Generated barcode image for coupon ID {coupon_id}")
    return barcode_data


def get_coupons(input_number: float) -> list:
    """
    Get coupon data based on input number.
    This is a placeholder function that returns hardcoded test data with 20-digit IDs.

    Args:
        input_number: The input number from the user

    Returns:
        List of coupon dictionaries with id, denomination, and barcode (BytesIO)
    """
    # Placeholder implementation with hardcoded test data using 20-digit IDs
    coupon_ids = [
        "12345678901234567890",
        "98765432109876543210",
        "11111111112222222222",
        "33333333334444444444",
        "55555555556666666666",
        "77777777778888888888"
    ]

    test_coupons = []
    denominations = [50, 100, 200, 300, 500, 1000]

    for i, coupon_id in enumerate(coupon_ids):
        coupon_data = {
            "id": coupon_id,
            "denomination": denominations[i],
            "barcode": generate_barcode(coupon_id, denominations[i])
        }
        test_coupons.append(coupon_data)

    logger.info(f"Retrieved {len(test_coupons)} coupons for input {input_number}")
    return test_coupons


def handle_coupon_accept(coupon_data: dict) -> None:
    """
    Handle accepting a coupon.
    Placeholder function for future implementation.

    Args:
        coupon_data: Dictionary containing coupon information
    """
    logger.info(f"Accepting coupon {coupon_data['id']} with denomination {coupon_data['denomination']}")
    # TODO: Implement coupon acceptance logic


def handle_coupon_decline(coupon_data: dict) -> None:
    """
    Handle declining a coupon.
    Placeholder function for future implementation.

    Args:
        coupon_data: Dictionary containing coupon information
    """
    logger.info(f"Declining coupon {coupon_data['id']} with denomination {coupon_data['denomination']}")
    # TODO: Implement coupon decline logic


@require_authorization
async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /pay command with optional number parameter.
    Only authorized users can use this command.

    Usage:
        /pay <number> - Shows coupon data with interactive buttons
        /pay - Returns usage instructions

    Args:
        update: The incoming update from Telegram
        context: The context object containing bot data
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if a parameter was provided
    if not context.args:
        # No parameter provided
        await context.bot.send_message(chat_id=chat_id, text="Please provide an input. Usage: /pay <input>")
        logger.info(f"User {user_id} used /pay without parameter")
        return

    # Get the first argument (accept any input for coupon processing)
    input_number = float(context.args[0])
    try:
        # Get coupon data
        coupons = get_coupons(input_number)

        if not coupons:
            await context.bot.send_message(chat_id=chat_id, text="No coupons found for the given input.")
            logger.info(f"No coupons found for input {input_number}")
            return

        sent_messages = []
        i = 0
        while i < len(coupons):
            try:
                coupon = coupons[i]

                # Create coupon message with shekel currency (without barcode text since it will be sent as image)
                coupon_message = f"Coupon ID: {coupon['id']}\nDenomination: ₪{coupon['denomination']}"

                # Create Accept/Decline buttons for this coupon
                keyboard = [
                    [
                        InlineKeyboardButton("Accept", callback_data=f"accept_coupon_{coupon['id']}"),
                        InlineKeyboardButton("Decline", callback_data=f"decline_coupon_{coupon['id']}")
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Send the coupon image and message
                await context.bot.send_photo(chat_id=chat_id, photo=coupon['barcode'])
                sent_msg = await context.bot.send_message(chat_id=chat_id, text=coupon_message, reply_markup=reply_markup)
                sent_messages.append(sent_msg)

                await asyncio.sleep(1)

                # Register message state
                MESSAGE_STATES[sent_msg.message_id] = {
                    "coupon_id": coupon['id'],
                    "coupon_data": coupon,
                    "status": "unprocessed"
                }
                i += 1
            except RetryAfter as e:
                logger.warning(
                    f"Failed to send coupon data {i + 1}/{len(coupons)} due to rate limited, sleeping for {e.retry_after} seconds")
                await asyncio.sleep(e.retry_after)

        # Send global control message with Accept All / Decline All buttons
        # Use shorter message IDs only for global actions to avoid callback data length limits
        global_message = f"Global actions for coupons (input: {input_number}):"
        msg_ids = ",".join([str(msg.message_id) for msg in sent_messages])
        global_keyboard = [
            [
                InlineKeyboardButton("Accept All", callback_data=f"accept_all_{input_number}_{msg_ids}"),
                InlineKeyboardButton("Decline All", callback_data=f"decline_all_{input_number}_{msg_ids}")
            ]
        ]
        global_reply_markup = InlineKeyboardMarkup(global_keyboard)

        await context.bot.send_message(chat_id=chat_id, text=global_message, reply_markup=global_reply_markup)
        logger.info(f"User {user_id} used /pay {input_number}, sent {len(coupons)} coupon messages with buttons")

    except Exception as e:
        # Error processing request
        await context.bot.send_message(chat_id=chat_id, text="Error processing your request. Please try again.")
        logger.error(f"Error processing /pay {input_number} for user {user_id}: {e}", exc_info=True)

@require_authorization
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle button callback queries.
    Only authorized users can interact with buttons.
    Supports Accept/Decline buttons and Accept All/Decline All functionality.

    Args:
        update: The incoming update from Telegram
        context: The context object containing bot data
    """
    query = update.callback_query
    user_id = update.effective_user.id

    # Parse the callback data
    callback_data = query.data

    # Check global actions first (more specific)
    if callback_data.startswith("accept_all_") or callback_data.startswith("decline_all_"):
        await handle_global_choice(query, user_id, callback_data, context)
    elif callback_data.startswith("accept_coupon_") or callback_data.startswith("decline_coupon_"):
        await handle_individual_choice(query, user_id, callback_data)
    elif callback_data.startswith("disabled_"):
        # Handle clicks on already disabled buttons
        await query.answer("This option was already processed.")
        logger.info(f"User {user_id} clicked on disabled button")
    else:
        logger.warning(f"Unknown callback data: {callback_data}")
        await query.answer("❌ Unknown selection.")


async def handle_individual_choice(query, user_id: int, callback_data: str) -> None:
    """
    Handle individual Accept/Decline button clicks for coupons.

    Args:
        query: The callback query object
        user_id: ID of the user who clicked the button
        callback_data: The callback data from the button
    """
    try:
        # Extract action and coupon ID from callback data
        # Format: "accept_coupon_{coupon_id}" or "decline_coupon_{coupon_id}"
        parts = callback_data.split("_", 2)
        action = parts[0]  # "accept" or "decline"
        # parts[1] is "coupon"
        coupon_id = parts[2]

        # Check if this message is already processed using our state tracking
        msg_id = query.message.message_id
        if msg_id in MESSAGE_STATES and MESSAGE_STATES[msg_id]["status"] != "unprocessed":
            # Message already processed, just acknowledge and return
            await query.answer("This option was already processed.")
            logger.info(f"User {user_id} tried to click already processed coupon {coupon_id} button")
            return

        # Get coupon data from message state
        coupon_data = MESSAGE_STATES[msg_id]["coupon_data"]

        # Acknowledge the callback query
        await query.answer()

        # Create disabled buttons based on action
        if action == "accept":
            disabled_button_text = f"✓ Accepted {coupon_id}"
            response = f"You accepted coupon {coupon_id} (₪{coupon_data['denomination']})"
            # Call coupon accept handler
            handle_coupon_accept(coupon_data)
        else:  # decline
            disabled_button_text = f"✗ Declined {coupon_id}"
            response = f"You declined coupon {coupon_id} (₪{coupon_data['denomination']})"
            # Call coupon decline handler
            handle_coupon_decline(coupon_data)

        # Create disabled button layout (use message ID to keep callback data short)
        disabled_keyboard = [[InlineKeyboardButton(disabled_button_text, callback_data=f"disabled_{msg_id}")]]
        disabled_markup = InlineKeyboardMarkup(disabled_keyboard)

        # Edit the message to show the disabled button
        await query.edit_message_reply_markup(reply_markup=disabled_markup)

        # Update message state
        if msg_id in MESSAGE_STATES:
            MESSAGE_STATES[msg_id]["status"] = action  # "accept" or "decline"

        # Send response message
        await query.message.reply_text(response)
        logger.info(f"User {user_id} {action}ed coupon {coupon_id}, buttons disabled")

    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing callback data '{callback_data}': {e}")
        await query.answer("❌ Error processing your selection.")


async def handle_global_choice(query, user_id: int, callback_data: str, context=None) -> None:
    """
    Handle Accept All/Decline All button clicks for coupons.
    Updates all unprocessed individual coupon messages.

    Args:
        query: The callback query object
        user_id: ID of the user who clicked the button
        callback_data: The callback data from the button
        context: The context object containing bot data
    """
    try:
        # Extract action, input number, and message IDs from callback data
        # Format: "accept_all_{input}_{msg_id1,msg_id2,msg_id3}" or "decline_all_{input}_{msg_id1,msg_id2,msg_id3}"
        parts = callback_data.split("_", 3)
        action = parts[0]  # "accept" or "decline"
        # parts[1] is "all"
        input_number = parts[2]
        msg_ids_str = parts[3]  # "msg_id1,msg_id2,msg_id3"

        # Parse message IDs
        msg_ids = [int(msg_id) for msg_id in msg_ids_str.split(",")]

        chat_id = query.message.chat_id

        # Acknowledge the callback query
        await query.answer()

        # Update individual coupon messages
        updated_count = 0

        for msg_id in msg_ids:
            try:
                # Check if this message is already processed using our state tracking
                if msg_id in MESSAGE_STATES and MESSAGE_STATES[msg_id]["status"] != "unprocessed":
                    coupon_id = MESSAGE_STATES[msg_id]["coupon_id"]
                    logger.info(f"Skipping message {msg_id} for coupon {coupon_id} - already processed as {MESSAGE_STATES[msg_id]['status']}")
                    continue

                # Get coupon data from message state
                coupon_data = MESSAGE_STATES[msg_id]["coupon_data"]
                coupon_id = coupon_data["id"]

                # Create the disabled button based on action
                if action == "accept":
                    disabled_button_text = f"✓ Accepted {coupon_id}"
                    # Call coupon accept handler
                    handle_coupon_accept(coupon_data)
                else:  # decline
                    disabled_button_text = f"✗ Declined {coupon_id}"
                    # Call coupon decline handler
                    handle_coupon_decline(coupon_data)

                # Use shorter callback data for disabled buttons to avoid length limits
                disabled_keyboard = [[InlineKeyboardButton(disabled_button_text, callback_data=f"disabled_{msg_id}")]]
                disabled_markup = InlineKeyboardMarkup(disabled_keyboard)

                # Update the message
                try:
                    await context.bot.edit_message_reply_markup(
                        chat_id=chat_id,
                        message_id=msg_id,
                        reply_markup=disabled_markup
                    )

                    # Update message state
                    if msg_id in MESSAGE_STATES:
                        MESSAGE_STATES[msg_id]["status"] = action  # "accept" or "decline"

                    updated_count += 1
                    logger.info(f"Updated message {msg_id} for coupon {coupon_id} with {action}")
                except Exception as edit_error:
                    logger.info(f"Could not update message {msg_id} for coupon {coupon_id}: {edit_error}")

            except Exception as msg_error:
                logger.error(f"Error processing message {msg_id}: {msg_error}")

        # Disable the global buttons
        disabled_text = f"✓ {action.title()} All Applied" if action == "accept" else f"✗ {action.title()} All Applied"
        disabled_keyboard = [[InlineKeyboardButton(disabled_text, callback_data=f"disabled_global_{action}")]]
        disabled_markup = InlineKeyboardMarkup(disabled_keyboard)
        await query.edit_message_reply_markup(reply_markup=disabled_markup)

        # Send response message
        if updated_count > 0:
            response = f"You {action}ed all remaining coupons for input {input_number} ({updated_count} coupons updated)"
        else:
            response = f"You {action}ed all remaining coupons for input {input_number} (no coupons needed updating)"
        await query.message.reply_text(response)
        logger.info(f"User {user_id} {action}ed all remaining coupons for input {input_number}, updated {updated_count} messages")

    except (IndexError, ValueError) as e:
        logger.error(f"Error parsing callback data '{callback_data}': {e}")
        await query.answer("❌ Error processing your selection.")


def main() -> None:
    """
    Main function to set up and run the Telegram bot.

    Note: While handlers are async, the main application runs synchronously
    from the user's perspective using run_polling().
    """
    try:
        # Load configuration from environment
        config = BotConfig.from_environment()
        logger.info(f"Bot configuration loaded successfully. Authorized users: {len(config.allowed_user_ids)}")

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return

    # Create the Application instance without job queue to avoid compatibility issues
    application = Application.builder().token(config.bot_token).job_queue(None).build()

    # Store configuration in application context for handlers to access
    application.bot_data['config'] = config

    # Add the /pay command handler
    pay_handler = CommandHandler('pay', pay_command)
    application.add_handler(pay_handler)

    # Add the callback query handler for button interactions
    callback_handler = CallbackQueryHandler(button_callback)
    application.add_handler(callback_handler)

    logger.info("Bot is starting...")

    # Start the bot using polling
    # This runs synchronously from the user's perspective
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
