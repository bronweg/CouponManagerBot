import asyncio
import json
import logging
from io import BytesIO
from json import JSONDecodeError

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import RetryAfter
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /balance command to show the user's coupon balance.
    Args:
        update: The update containing the command.
        context: The context of the command, including bot data.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    logger.info(f"User {user_id} requested coupons balance in chat {chat_id}.")

    provider = context.application.bot_data["coupon_provider"]
    # Get the current balance from the provider
    balance = provider.get_balance()

    balance_summary = "\n".join([f"{amount} of {denominal}₪" for denominal, amount in balance])

    await context.bot.send_message(chat_id=chat_id, text=f"Total coupons available:\n{balance_summary}")


async def json_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /json command to add coupons in JSON format.
    Args:
        update: The update containing the command.
        context: The context of the command, including bot data.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    logger.info(f"User {user_id} requested to add coupons in JSON format from chat {chat_id}.")

    # Get the amount to pay as a float number from the command arguments and issue warning if not provided
    try:
        coupons_json = json.loads("".join(context.args))
    except (JSONDecodeError, IndexError):
        logger.error(f"User {user_id} provided invalid JSON to add coupons: {context.args}")
        await update.message.reply_text("Please provide a valid JSON with coupons.")
        return

    provider = context.application.bot_data["coupon_provider"]

    try:
        # Insert the coupons into the provider
        inserted_count = provider.insert_eternal_coupons(coupons_json)
        if inserted_count > 0:
            await update.message.reply_text(f"Successfully added {inserted_count} coupons.")
            logger.info(f"User {user_id} added {inserted_count} coupons from JSON in chat {chat_id}.")
        else:
            await update.message.reply_text("No coupons were added. Please check the JSON format.")
            logger.warning(f"User {user_id} tried to add coupons but none were added in chat {chat_id}.")
    except Exception as e:
        logger.error(f"Error while adding coupons from JSON: {e}")
        await update.message.reply_text("An error occurred while adding coupons. Please check the JSON format and try again.")
        return


async def issue_single_coupon(
        chat_id: int, coupon_id: int, coupon_barcode: BytesIO, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Issues a single coupon to the user with Accept/Decline buttons.
    Args:
        chat_id: The ID of the chat where the coupon will be sent.
        coupon_id: The ID of the coupon to be issued.
        coupon_barcode: The barcode image of the coupon.
        context: The context of the command, including bot data.
    Returns:
        The message ID of the sent coupon message.
    """
    # Create Accept/Decline buttons for this coupon
    keyboard = [
        [
            InlineKeyboardButton("Accept", callback_data=f"accept_coupon_{coupon_id}"),
            InlineKeyboardButton("Decline", callback_data=f"decline_coupon_{coupon_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the coupon image and message
    sent_msg = await context.bot.send_photo(chat_id=chat_id, photo=coupon_barcode, reply_markup=reply_markup)
    await asyncio.sleep(1)

    return sent_msg.message_id


async def issue_coupons_summary(
        chat_id: int, cash_to_add: float, bunch_id: str, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Issues a summary message with the total amount to add and Accept/Decline buttons for all coupons.
    Args:
        chat_id: The ID of the chat where the summary will be sent.
        cash_to_add: The total amount to add based on the issued coupons.
        bunch_id: The ID of the bunch to which the coupons belong.
        context: The context of the command, including bot data.
    """
    # Create Accept/Decline buttons for all coupons
    global_keyboard = [
        [
            InlineKeyboardButton("Accept All", callback_data=f"accept_all_{bunch_id}"),
            InlineKeyboardButton("Decline All", callback_data=f"decline_all_{bunch_id}")
        ]
    ]
    global_reply_markup = InlineKeyboardMarkup(global_keyboard)

    # Send the summary message with the amount to add and buttons
    global_message = f"The amount to add is **{cash_to_add}₪**.\n"
    await context.bot.send_message(chat_id=chat_id, text=global_message, reply_markup=global_reply_markup)



async def pay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /pay command to process a payment and issue coupons.
    Args:
        update: The update containing the command.
        context: The context of the command, including bot data.
    """
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message_id = update.message.message_id
    bunch_id = f"{chat_id}:{message_id}"

    logger.info(f"User {user_id} requested payment in chat {chat_id}.")

    # Get the amount to pay as a float number from the command arguments and issue warning if not provided
    try:
        amount_to_pay = float(context.args[0])
    except (ValueError, IndexError):
        logger.error(f"User {user_id} provided invalid amount to pay: {context.args}")
        await update.message.reply_text("Please provide a valid amount to pay.")
        return

    provider = context.application.bot_data["coupon_provider"]

    # Get the bunch ID from the command arguments and issue warning if not provided
    try:
        logger.debug("Getting coupons for amount: %s, bunch_id: %s", amount_to_pay, bunch_id)
        cash_to_add, coupons_with_barcode = provider.get_coupons(amount_to_pay, bunch_id)
    except Exception as e:
        logger.error(f"Error while getting coupons: {e}")
        await update.message.reply_text("An error occurred while processing your payment. Please try again later.")
        return

    # Sending coupons to the user
    try:
        # Sending message per coupon
        i = 0
        while i < len(coupons_with_barcode):
            coupon_id, coupon_barcode = coupons_with_barcode[i]
            try:
                coupon_message_id = await issue_single_coupon(chat_id, coupon_id, coupon_barcode, context)
            except RetryAfter as e:
                logger.warning(
                               f"Failed to send coupon data {i + 1}/{len(coupons_with_barcode)} due to rate limited, "
                               f"sleeping for {e.retry_after} seconds"
                )
                await asyncio.sleep(e.retry_after)
                continue

            provider.set_coupon_processing_id(coupon_id, coupon_message_id)
            i += 1

        # Sending global message
        await issue_coupons_summary(chat_id, cash_to_add, bunch_id, context)

        logger.info(
            f"User {user_id} used `/pay {amount_to_pay}`, sent {len(coupons_with_barcode)} coupon messages with buttons"
        )
    except Exception as e:
        logger.error(f"Error while sending coupons: {e}")
        # Release all reserved coupons if an error occurs
        try:
            provider.reject_coupons(bunch_id, ignore_processing_id=True)
        except Exception as release_error:
            logger.error(
                f"Error while releasing reserved coupons: {release_error}. Manual intervention may be required."
            )
        await update.message.reply_text("An error occurred while sending your coupons. Please try again later.")
        return


async def handle_coupon_accept(query, user_id, coupon_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the acceptance of a single coupon.
    Args:
        query: The callback query containing the user's action.
        user_id: The ID of the user who accepted the coupon.
        coupon_id: The ID of the coupon being accepted.
        context: The context of the callback query, including bot data.
    """
    logger.debug(f"User {user_id} - accepting coupon {coupon_id}")
    provider = context.application.bot_data["coupon_provider"]
    try:
        processing_id = provider.use_coupon(coupon_id)
        await query.answer(f"✅ Coupon {coupon_id} accepted. Processing ID: {processing_id}")

        logger.info(f"User {user_id} accepted coupon {coupon_id}. Processing ID: {processing_id}")
        await query.edit_message_caption(
            caption=f"✅ Coupon accepted.",
        )
    except Exception as e:
        logger.error(f"Error accepting coupon {coupon_id}: {e}")
        await query.answer("❌ Failed to accept the coupon. Please try again later.", show_alert=True)


async def handle_coupon_decline(query, user_id, coupon_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the decline of a single coupon.
    Args:
        query: The callback query containing the user's action.
        user_id: The ID of the user who declined the coupon.
        coupon_id: The ID of the coupon being declined.
        context: The context of the callback query, including bot data.
    """
    logger.debug(f"User {user_id} - accepting coupon {coupon_id}")
    provider = context.application.bot_data["coupon_provider"]
    try:
        processing_id = provider.reject_coupon(coupon_id)
        await query.answer(f"↩️ Coupon {coupon_id} declined. Processing ID: {processing_id}.")

        logger.info(f"User {user_id} declined coupon {coupon_id}. Processing ID: {processing_id}.")
        await query.edit_message_caption(
            caption=f"↩️ Coupon declined.",
        )
    except Exception as e:
        logger.error(f"Error declining coupon {coupon_id}: {e}")
        await query.answer("❌ Failed to decline the coupon. Please try again later.", show_alert=True)


async def handle_coupon_action(query, user_id, callback_data, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the acceptance or decline of a single coupon based on the callback data.
    Args:
        query: The callback query containing the user's action.
        user_id: The ID of the user who performed the action.
        callback_data: The data from the callback query indicating the action and coupon ID.
        context: The context of the callback query, including bot data.
    """
    try:
        # Format: "accept_coupon_{coupon_id}" or "decline_coupon_{coupon_id}"
        action, _, coupon_id = callback_data.split("_", 2)
    except ValueError:
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.answer("❌ Invalid selection format.", show_alert=True)
        return

    if action == "accept":
        await handle_coupon_accept(query, user_id, coupon_id, context)
    elif action == "decline":
        await handle_coupon_decline(query, user_id, coupon_id, context)
    else:
        logger.warning(f"Unknown action in coupon action: {action}")
        await query.answer("❌ Unknown action.", show_alert=True)
        return


async def handle_coupons_accept(query, user_id, bunch_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the acceptance of all coupons in a bunch.
    Args:
        query: The callback query containing the user's action.
        user_id: The ID of the user who accepted the coupons.
        bunch_id: The ID of the bunch containing the coupons.
        context: The context of the callback query, including bot data.
    """
    logger.debug(f"User {user_id} - accepting coupons {bunch_id}")
    provider = context.application.bot_data["coupon_provider"]
    try:
        processing_ids = provider.use_coupons(bunch_id)

        if not processing_ids:
            await query.answer("❌ All coupons in this bunch have already been accepted or declined.")
        else:
            await query.answer(f"✅ Remaining {len(processing_ids)} in bunch {bunch_id} accepted.")

            logger.info(f"User {user_id} accepting coupons in bunch {bunch_id}. Processing IDs: {processing_ids}")


            for processing_id in processing_ids:
                try:
                    # Edit the message with the coupon ID to indicate acceptance
                    await context.bot.edit_message_caption(
                        chat_id=query.message.chat_id,
                        message_id=processing_id,
                        caption=f"✅ Coupon accepted.",
                    )
                except Exception as e:
                    logger.error(f"Error editing message for processing ID {processing_id}: {e}")

        await query.edit_message_text(
            text=f"{query.message.text}\n\n🐾 All coupons in bunch were accepted/rejected.",
        )
    except Exception as e:
        logger.error(f"Error accepting coupons in bunch {bunch_id}: {e}")
        await query.answer("❌ Failed to accept the coupons. Please try again later.", show_alert=True)


async def handle_coupons_decline(query, user_id, bunch_id, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the decline of all coupons in a bunch.
    Args:
        query: The callback query containing the user's action.
        user_id: The ID of the user who declined the coupons.
        bunch_id: The ID of the bunch containing the coupons.
        context: The context of the callback query, including bot data.
    """
    logger.debug(f"User {user_id} - declining coupons {bunch_id}")
    provider = context.application.bot_data["coupon_provider"]
    try:
        processing_ids = provider.reject_coupons(bunch_id, ignore_processing_id=True)

        if not processing_ids:
            await query.answer("❌ All coupons in this bunch have already been accepted or declined.")
        else:
            await query.answer(f"↩️ Remaining {len(processing_ids)} in bunch {bunch_id} declined.")

            logger.info(f"User {user_id} declining coupons in bunch {bunch_id}. Processing IDs: {processing_ids}")

            bot = context.bot
            for processing_id in processing_ids:
                try:
                    # Edit the message with the coupon ID to indicate decline
                    await bot.edit_message_caption(
                        chat_id=query.message.chat_id,
                        message_id=processing_id,
                        caption=f"↩️ Coupon declined.",
                    )
                except Exception as e:
                    logger.error(f"Error editing message for processing ID {processing_id}: {e}")

        await query.edit_message_text(
            text=f"{query.message.text}\n\n🐾 All coupons in bunch were accepted/rejected.",
        )
    except Exception as e:
        logger.error(f"Error declining coupons in bunch {bunch_id}: {e}")
        await query.answer("❌ Failed to decline the coupons. Please try again later.", show_alert=True)


async def handle_coupons_action(query, user_id, callback_data, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the acceptance or decline of all coupons in a bunch based on the callback data.
    Args:
        query: The callback query containing the user's action.
        user_id: The ID of the user who performed the action.
        callback_data: The data from the callback query indicating the action and bunch ID.
        context: The context of the callback query, including bot data.
    """
    try:
        # Format: "accept_all_{bunch_id}" or "decline_all_{bunch_id}"
        action, _, bunch_id = callback_data.split("_", 2)
    except ValueError:
        logger.error(f"Invalid callback data format: {callback_data}")
        await query.answer("❌ Invalid selection format.", show_alert=True)
        return

    if action == "accept":
        await handle_coupons_accept(query, user_id, bunch_id, context)
    elif action == "decline":
        await handle_coupons_decline(query, user_id, bunch_id, context)
    else:
        logger.warning(f"Unknown action in coupons action: {action}")
        await query.answer("❌ Unknown action.", show_alert=True)
        return


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button callback queries for accepting or declining coupons.
    Args:
        update: The update containing the callback query.
        context: The context of the callback query, including bot data.
    """
    logger.debug(f"Received callback query: {update.callback_query.data}")

    query = update.callback_query
    user_id = update.effective_user.id

    # Parse the callback data
    callback_data = query.data

    # Call the appropriate handler based on the callback data
    if callback_data.startswith("accept_all_") or callback_data.startswith("decline_all_"):
        await handle_coupons_action(query, user_id, callback_data, context)
    elif callback_data.startswith("accept_coupon_") or callback_data.startswith("decline_coupon_"):
        await handle_coupon_action(query, user_id, callback_data, context)
    else:
        logger.warning(f"Unknown callback data: {callback_data}")
        await query.answer("❌ Unknown selection.", show_alert=True)




