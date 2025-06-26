#!/usr/bin/env python3
"""
Simple test script to verify the bot functionality.
"""

import os
import sys
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_bot_token_loading():
    """Test that the bot token can be loaded from environment variables."""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable is not set!")
        print("Please set it in your .env.local file")
        return False
    
    if bot_token == 'your_bot_token_here':
        print("❌ TELEGRAM_BOT_TOKEN is still set to the default placeholder value!")
        print("Please set a real bot token in your .env.local file")
        return False
    
    print("✅ Bot token loaded successfully")
    return True


def test_ping_command_with_number():
    """Test the ping command handler with a valid number."""
    try:
        # Import the bot module
        import bot
        import asyncio

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()
        mock_chat = Mock()

        # Set up the mock structure
        mock_update.message = mock_message
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"
        mock_update.effective_chat = mock_chat
        mock_update.effective_chat.id = 12345

        # Mock the context and bot
        mock_context.bot = mock_bot
        mock_context.args = ["5"]  # Simulate /ping 5

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async send_message method
        from unittest.mock import AsyncMock

        # Create mock message objects with message_id attributes
        mock_sent_msg_1 = Mock()
        mock_sent_msg_1.message_id = 123
        mock_sent_msg_2 = Mock()
        mock_sent_msg_2.message_id = 124
        mock_sent_msg_3 = Mock()
        mock_sent_msg_3.message_id = 125
        mock_sent_msg_4 = Mock()
        mock_sent_msg_4.message_id = 126

        # Set up send_message and send_photo to return different mock messages for each call
        from unittest.mock import AsyncMock
        mock_bot.send_message = AsyncMock(side_effect=[mock_sent_msg_1, mock_sent_msg_2, mock_sent_msg_3, mock_sent_msg_4])
        mock_bot.send_photo = AsyncMock()

        # Run the async ping command
        asyncio.run(bot.ping_command(mock_update, mock_context))

        # Check if send_message was called four times (three coupons + global controls)
        assert mock_bot.send_message.call_count == 4

        # Check if send_photo was called three times (one for each coupon barcode)
        assert mock_bot.send_photo.call_count == 3

        # Get all the call arguments
        call_args_list = mock_bot.send_message.call_args_list

        # Check first message: Coupon with 20-digit ID with Accept/Decline buttons (shekel currency)
        first_call = call_args_list[0][1]
        assert "Coupon ID: 12345678901234567890" in first_call['text']
        assert "Denomination: ₪50" in first_call['text']
        assert "Barcode:" not in first_call['text']  # No barcode text since it's sent as image
        assert 'reply_markup' in first_call

        # Check second message: Coupon with 20-digit ID with Accept/Decline buttons (shekel currency)
        second_call = call_args_list[1][1]
        assert "Coupon ID: 98765432109876543210" in second_call['text']
        assert "Denomination: ₪100" in second_call['text']
        assert "Barcode:" not in second_call['text']  # No barcode text since it's sent as image
        assert 'reply_markup' in second_call

        # Check third message: Coupon with 20-digit ID with Accept/Decline buttons (shekel currency)
        third_call = call_args_list[2][1]
        assert "Coupon ID: 11111111112222222222" in third_call['text']
        assert "Denomination: ₪200" in third_call['text']
        assert "Barcode:" not in third_call['text']  # No barcode text since it's sent as image
        assert 'reply_markup' in third_call

        # Check fourth message: Global controls with Accept All/Decline All buttons
        fourth_call = call_args_list[3][1]
        assert "Global actions for coupons" in fourth_call['text']
        assert "input: 5" in fourth_call['text']
        assert 'reply_markup' in fourth_call

        print("✅ Ping command with number works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing ping command with number: {e}")
        return False


def test_ping_command_no_parameter():
    """Test the ping command handler without parameter."""
    try:
        # Import the bot module
        import bot
        import asyncio

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()
        mock_chat = Mock()

        # Set up the mock structure
        mock_update.message = mock_message
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"
        mock_update.effective_chat = mock_chat
        mock_update.effective_chat.id = 12345

        # Mock the context and bot
        mock_context.bot = mock_bot
        mock_context.args = []  # Simulate /ping without parameter

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async send_message method
        from unittest.mock import AsyncMock
        mock_bot.send_message = AsyncMock(return_value="usage")

        # Run the async ping command
        asyncio.run(bot.ping_command(mock_update, mock_context))

        # Check if send_message was called with usage message
        mock_bot.send_message.assert_called_once()
        call_args = mock_bot.send_message.call_args
        assert "Usage:" in call_args[1]['text']

        print("✅ Ping command without parameter works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing ping command without parameter: {e}")
        return False


def test_unauthorized_user():
    """Test that unauthorized users are rejected."""
    try:
        # Import the bot module
        import bot
        import asyncio

        # Create test configuration - only user 12345 is allowed
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects for unauthorized user
        mock_update = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()
        mock_chat = Mock()

        # Set up the mock structure for unauthorized user
        mock_update.message = mock_message
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 99999  # Unauthorized user
        mock_update.effective_user.username = "unauthorized"
        mock_update.effective_chat = mock_chat
        mock_update.effective_chat.id = 99999

        # Mock the context and bot
        mock_context.bot = mock_bot

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async methods
        from unittest.mock import AsyncMock
        mock_bot.send_message = AsyncMock(return_value="unauthorized")
        mock_message.reply_text = AsyncMock(return_value="unauthorized")

        # Run the async ping command
        asyncio.run(bot.ping_command(mock_update, mock_context))

        # Check if unauthorized message was sent
        if mock_message.reply_text.called:
            call_args = mock_message.reply_text.call_args[0][0]
            if "not authorized" in call_args:
                print("✅ Unauthorized user handling works correctly")
                return True

        print("❌ Unauthorized user was not properly rejected")
        return False

    except Exception as e:
        print(f"❌ Error testing unauthorized user: {e}")
        return False


def test_ping_command_invalid_number():
    """Test the ping command handler with invalid number."""
    try:
        # Import the bot module
        import bot
        import asyncio

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()
        mock_chat = Mock()

        # Set up the mock structure
        mock_update.message = mock_message
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"
        mock_update.effective_chat = mock_chat
        mock_update.effective_chat.id = 12345

        # Mock the context and bot
        mock_context.bot = mock_bot
        mock_context.args = ["abc"]  # Simulate /ping abc

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Create mock message objects with message_id attributes for coupon messages
        mock_sent_msg_1 = Mock()
        mock_sent_msg_1.message_id = 126
        mock_sent_msg_2 = Mock()
        mock_sent_msg_2.message_id = 127
        mock_sent_msg_3 = Mock()
        mock_sent_msg_3.message_id = 128
        mock_sent_msg_4 = Mock()
        mock_sent_msg_4.message_id = 129

        # Mock the async send_message and send_photo methods
        from unittest.mock import AsyncMock
        mock_bot.send_message = AsyncMock(side_effect=[mock_sent_msg_1, mock_sent_msg_2, mock_sent_msg_3, mock_sent_msg_4])
        mock_bot.send_photo = AsyncMock()

        # Run the async ping command
        asyncio.run(bot.ping_command(mock_update, mock_context))

        # Check if send_message was called 4 times (3 coupons + 1 global message)
        assert mock_bot.send_message.call_count == 4

        # Check if send_photo was called 3 times (one for each coupon barcode)
        assert mock_bot.send_photo.call_count == 3

        print("✅ Ping command with any input works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing ping command with any input: {e}")
        return False


def test_button_callback_accept():
    """Test the accept button callback handler."""
    try:
        # Import the bot module
        import bot
        import asyncio
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_callback_query = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()

        # Set up the mock structure for callback query
        mock_update.callback_query = mock_callback_query
        mock_update.message = None  # No message for callback queries
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"

        # Mock callback query data for accept coupon
        mock_callback_query.data = "accept_coupon_12345678901234567890"
        mock_callback_query.message = mock_message
        mock_message.message_id = 123  # Set message ID for state tracking

        # Set up message state for coupon with 20-digit ID
        from io import BytesIO
        test_barcode = BytesIO(b"BARCODE:12345678901234567890")
        bot.MESSAGE_STATES[123] = {
            "coupon_id": "12345678901234567890",
            "coupon_data": {"id": "12345678901234567890", "denomination": "50", "barcode": test_barcode},
            "status": "unprocessed"
        }

        # Mock the current reply markup (buttons not yet clicked)
        accept_button = InlineKeyboardButton("Accept", callback_data="accept_coupon_12345678901234567890")
        decline_button = InlineKeyboardButton("Decline", callback_data="decline_coupon_12345678901234567890")
        original_markup = InlineKeyboardMarkup([[accept_button, decline_button]])
        mock_message.reply_markup = original_markup

        # Mock the context and bot
        mock_context.bot = mock_bot

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async methods
        from unittest.mock import AsyncMock
        mock_callback_query.answer = AsyncMock()
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_message.reply_text = AsyncMock(return_value="You accepted 10")

        # Run the async button callback
        asyncio.run(bot.button_callback(mock_update, mock_context))

        # Check if callback was answered, button was disabled, and reply was sent (shekel currency)
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_reply_markup.assert_called_once()
        mock_message.reply_text.assert_called_once_with("You accepted coupon 12345678901234567890 (₪50)")

        # Clean up the test state
        if 123 in bot.MESSAGE_STATES:
            del bot.MESSAGE_STATES[123]

        print("✅ Accept button callback works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing accept button callback: {e}")
        return False


def test_button_callback_decline():
    """Test the decline button callback handler."""
    try:
        # Import the bot module
        import bot
        import asyncio
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_callback_query = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()

        # Set up the mock structure for callback query
        mock_update.callback_query = mock_callback_query
        mock_update.message = None  # No message for callback queries
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"

        # Mock callback query data for decline coupon
        mock_callback_query.data = "decline_coupon_98765432109876543210"
        mock_callback_query.message = mock_message
        mock_message.message_id = 124  # Set message ID for state tracking

        # Set up message state for coupon with 20-digit ID
        from io import BytesIO
        test_barcode = BytesIO(b"BARCODE:98765432109876543210")
        bot.MESSAGE_STATES[124] = {
            "coupon_id": "98765432109876543210",
            "coupon_data": {"id": "98765432109876543210", "denomination": "100", "barcode": test_barcode},
            "status": "unprocessed"
        }

        # Mock the current reply markup (buttons not yet clicked)
        accept_button = InlineKeyboardButton("Accept", callback_data="accept_coupon_98765432109876543210")
        decline_button = InlineKeyboardButton("Decline", callback_data="decline_coupon_98765432109876543210")
        original_markup = InlineKeyboardMarkup([[accept_button, decline_button]])
        mock_message.reply_markup = original_markup

        # Mock the context and bot
        mock_context.bot = mock_bot

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async methods
        from unittest.mock import AsyncMock
        mock_callback_query.answer = AsyncMock()
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_message.reply_text = AsyncMock(return_value="You declined 15")

        # Run the async button callback
        asyncio.run(bot.button_callback(mock_update, mock_context))

        # Check if callback was answered, button was disabled, and reply was sent (shekel currency)
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_reply_markup.assert_called_once()
        mock_message.reply_text.assert_called_once_with("You declined coupon 98765432109876543210 (₪100)")

        # Clean up the test state
        if 124 in bot.MESSAGE_STATES:
            del bot.MESSAGE_STATES[124]

        print("✅ Decline button callback works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing decline button callback: {e}")
        return False


def test_button_callback_accept_all():
    """Test the accept all button callback handler."""
    try:
        # Import the bot module
        import bot
        import asyncio
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_callback_query = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()

        # Set up the mock structure for callback query
        mock_update.callback_query = mock_callback_query
        mock_update.message = None  # No message for callback queries
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"

        # Mock callback query data for accept all coupons (with message IDs only)
        mock_callback_query.data = "accept_all_5_123,124,125"
        mock_callback_query.message = mock_message
        mock_callback_query.bot = mock_bot

        # Mock message properties
        mock_message.chat_id = 12345

        # Set up message states for coupons with 20-digit IDs
        from io import BytesIO
        test_barcode_1 = BytesIO(b"BARCODE:12345678901234567890")
        test_barcode_2 = BytesIO(b"BARCODE:98765432109876543210")
        test_barcode_3 = BytesIO(b"BARCODE:11111111112222222222")

        bot.MESSAGE_STATES[123] = {
            "coupon_id": "12345678901234567890",
            "coupon_data": {"id": "12345678901234567890", "denomination": "50", "barcode": test_barcode_1},
            "status": "unprocessed"
        }
        bot.MESSAGE_STATES[124] = {
            "coupon_id": "98765432109876543210",
            "coupon_data": {"id": "98765432109876543210", "denomination": "100", "barcode": test_barcode_2},
            "status": "unprocessed"
        }
        bot.MESSAGE_STATES[125] = {
            "coupon_id": "11111111112222222222",
            "coupon_data": {"id": "11111111112222222222", "denomination": "200", "barcode": test_barcode_3},
            "status": "unprocessed"
        }

        # Mock the current reply markup (global buttons not yet clicked)
        accept_all_button = InlineKeyboardButton("Accept All", callback_data="accept_all_5_123,124,125")
        decline_all_button = InlineKeyboardButton("Decline All", callback_data="decline_all_5_123,124,125")
        original_markup = InlineKeyboardMarkup([[accept_all_button, decline_all_button]])
        mock_message.reply_markup = original_markup

        # Mock the context and bot
        mock_context.bot = mock_bot

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async methods
        from unittest.mock import AsyncMock
        mock_callback_query.answer = AsyncMock()
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_bot.edit_message_reply_markup = AsyncMock()  # For updating individual messages
        mock_message.reply_text = AsyncMock()

        # Run the async button callback
        asyncio.run(bot.button_callback(mock_update, mock_context))

        # Check if callback was answered, buttons were updated, and reply was sent
        mock_callback_query.answer.assert_called_once()
        mock_callback_query.edit_message_reply_markup.assert_called_once()  # Global message update
        assert mock_bot.edit_message_reply_markup.call_count == 3  # Three individual messages updated
        mock_message.reply_text.assert_called_once()

        # Check that the response message contains expected text
        call_args = mock_message.reply_text.call_args[0][0]
        assert "You accepted all remaining coupons for input 5" in call_args

        # Clean up the test state
        for msg_id in [123, 124, 125]:
            if msg_id in bot.MESSAGE_STATES:
                del bot.MESSAGE_STATES[msg_id]

        print("✅ Accept All button callback works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing Accept All button callback: {e}")
        return False


def test_button_callback_already_clicked():
    """Test the button callback handler when button is already clicked."""
    try:
        # Import the bot module
        import bot
        import asyncio
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup

        # Create test configuration
        test_config = bot.BotConfig(
            bot_token="test_token",
            allowed_user_ids={12345}
        )

        # Create mock objects
        mock_update = Mock()
        mock_callback_query = Mock()
        mock_message = Mock()
        mock_user = Mock()
        mock_context = Mock()
        mock_bot = Mock()

        # Set up the mock structure for callback query
        mock_update.callback_query = mock_callback_query
        mock_update.message = None  # No message for callback queries
        mock_update.effective_user = mock_user
        mock_update.effective_user.id = 12345  # Authorized user
        mock_update.effective_user.username = "testuser"

        # Mock callback query data
        mock_callback_query.data = "accept_coupon_12345678901234567890"
        mock_callback_query.message = mock_message
        mock_message.message_id = 123  # Set message ID for state tracking

        # Set up message state as already processed with 20-digit ID
        from io import BytesIO
        test_barcode = BytesIO(b"BARCODE:12345678901234567890")
        bot.MESSAGE_STATES[123] = {
            "coupon_id": "12345678901234567890",
            "coupon_data": {"id": "12345678901234567890", "denomination": "50", "barcode": test_barcode},
            "status": "accepted"  # Already processed
        }

        # Mock the current reply markup (button already clicked - has checkmark)
        disabled_button = InlineKeyboardButton("✓ Accepted 12345678901234567890", callback_data="disabled_coupon_12345678901234567890")
        disabled_markup = InlineKeyboardMarkup([[disabled_button]])
        mock_message.reply_markup = disabled_markup

        # Mock the context and bot
        mock_context.bot = mock_bot

        # Mock application and bot_data
        mock_application = Mock()
        mock_application.bot_data = {'config': test_config}
        mock_context.application = mock_application

        # Mock the async methods
        from unittest.mock import AsyncMock
        mock_callback_query.answer = AsyncMock()
        mock_callback_query.edit_message_reply_markup = AsyncMock()
        mock_message.reply_text = AsyncMock()

        # Run the async button callback
        asyncio.run(bot.button_callback(mock_update, mock_context))

        # Check that callback was answered with "already processed" message
        mock_callback_query.answer.assert_called_once_with("This option was already processed.")
        # Check that edit_message_reply_markup was NOT called (button already disabled)
        mock_callback_query.edit_message_reply_markup.assert_not_called()
        # Check that reply_text was NOT called (no new response message)
        mock_message.reply_text.assert_not_called()

        # Clean up the test state
        if 123 in bot.MESSAGE_STATES:
            del bot.MESSAGE_STATES[123]

        print("✅ Button callback already clicked handling works correctly")
        return True

    except Exception as e:
        print(f"❌ Error testing button callback already clicked: {e}")
        return False


def main():
    """Run all tests."""
    print("Testing Telegram Bot...")
    print("=" * 40)

    tests_passed = 0
    total_tests = 9

    # Test 1: Bot token loading
    if test_bot_token_loading():
        tests_passed += 1

    # Test 2: Ping command with valid number
    if test_ping_command_with_number():
        tests_passed += 1

    # Test 3: Ping command without parameter
    if test_ping_command_no_parameter():
        tests_passed += 1

    # Test 4: Ping command error handling
    if test_ping_command_invalid_number():
        tests_passed += 1

    # Test 5: Accept button callback handling
    if test_button_callback_accept():
        tests_passed += 1

    # Test 6: Decline button callback handling
    if test_button_callback_decline():
        tests_passed += 1

    # Test 7: Accept All button callback handling
    if test_button_callback_accept_all():
        tests_passed += 1

    # Test 8: Button callback already clicked handling
    if test_button_callback_already_clicked():
        tests_passed += 1

    # Test 9: Unauthorized user handling
    if test_unauthorized_user():
        tests_passed += 1

    print("=" * 40)
    print(f"Tests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Your bot is ready to run.")
        print("\nTo start the bot, run:")
        print("python bot.py")
        print("\n📋 Note: Make sure to set your user ID in ALLOWED_USER_IDS")
        print("📋 Usage: /ping <number> (e.g., /ping 5 → shows 3 coupons with Accept/Decline buttons + Accept All/Decline All)")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == '__main__':
    main()
