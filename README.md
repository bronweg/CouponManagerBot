# Minimal Telegram Bot

A simple Python Telegram bot using the `python-telegram-bot` library (version 20+). The main application runs synchronously using `run_polling()`, while handlers use async for compatibility with the library.

## Features

- **Coupon Management System** - Process and manage digital coupons with interactive controls
- **20-digit Coupon IDs** - Uses standardized 20-digit numeric coupon identifiers (e.g., "12345678901234567890")
- **Barcode Image Generation** - Automatic barcode generation and image sending for each coupon using BytesIO objects
- **Israeli Shekel Currency** - Uses ₪ (shekel) symbol for all denomination displays
- **Enhanced `/ping` command** - Shows coupon data with Accept/Decline buttons for each coupon
- **Accept/Decline buttons** - Each coupon has two options: Accept or Decline with dedicated handlers
- **Smart Global Actions** - Accept All/Decline All buttons automatically update all unprocessed individual coupons
- **Intelligent message tracking** - Global actions only affect coupons that haven't been processed yet
- **Single-use interactive buttons** - Buttons become disabled after first click to prevent duplicate responses
- **Visual feedback** - Clicked buttons show "✓ Accepted [20-digit ID]" or "✗ Declined [20-digit ID]" to indicate choice
- **Modular coupon system** - Placeholder functions for coupon acceptance and decline logic
- **User whitelist/authorization** - Only authorized users can use the bot
- **Flexible input handling** - Accepts any input parameter for coupon retrieval
- **Centralized configuration** - Clean configuration management with dataclasses
- **No global variables** - Configuration passed through application context
- Synchronous main application (uses `run_polling()` for blocking execution)
- Handlers use async for library compatibility
- Environment variable configuration
- Comprehensive error handling and logging

## Setup

1. **Install dependencies:**
   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment variables:**
   - Copy `.env.example` to `.env.local`
   - Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram
   - Set your `TELEGRAM_BOT_TOKEN` in `.env.local`
   - **Set authorized user IDs** in `ALLOWED_USER_IDS` (comma-separated)
     - Get your user ID by messaging [@userinfobot](https://t.me/userinfobot) on Telegram
     - Example: `ALLOWED_USER_IDS=123456789,987654321`

3. **Test the bot:**
   ```bash
   python test_bot.py
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Usage

Once the bot is running, you can interact with it on Telegram:

### `/ping` Command Examples:

**Input**: `/ping 5`
**Response** (seven separate messages):
1. `Coupon ID: 12345678901234567890\nDenomination: ₪50` + [Accept] [Decline] buttons
2. **Barcode image** (sent as photo)
3. `Coupon ID: 98765432109876543210\nDenomination: ₪100` + [Accept] [Decline] buttons
4. **Barcode image** (sent as photo)
5. `Coupon ID: 11111111112222222222\nDenomination: ₪200` + [Accept] [Decline] buttons
6. **Barcode image** (sent as photo)
7. `Global actions for coupons (input: 5):` + [Accept All] [Decline All] buttons

**Button Interactions**:
- Click "Accept" → "You accepted coupon 12345678901234567890 (₪50)" + button changes to "✓ Accepted 12345678901234567890"
- Click "Decline" → "You declined coupon 98765432109876543210 (₪100)" + button changes to "✗ Declined 98765432109876543210"
- Click "Accept All" → "You accepted all remaining coupons for input 5" + **automatically updates all unprocessed individual coupons** to show "✓ Accepted [20-digit ID]"
- Click "Decline All" → "You declined all remaining coupons for input 5" + **automatically updates all unprocessed individual coupons** to show "✗ Declined [20-digit ID]"
- **Smart updates**: Global actions only affect coupons that haven't been processed yet
- Subsequent clicks on processed buttons → "This option was already processed." (no new message)

**Other Examples**:
- `/ping abc` → Four messages: three coupons with Accept/Decline buttons + global controls
- `/ping 123` → Four messages: three coupons with Accept/Decline buttons + global controls
- `/ping` → "Please provide a number. Usage: /ping <number>"
- `/ping abc` → "Invalid number. Please provide a valid number."

**Note**: Only authorized users can use bot commands and interact with buttons. Unauthorized users will receive a "not authorized" message.

## Security

The bot includes user authorization features:
- Only users listed in `ALLOWED_USER_IDS` can use bot commands
- Unauthorized access attempts are logged
- Clear error messages for unauthorized users

## Project Structure

- `bot.py` - Main bot implementation
- `requirements.txt` - Python dependencies
- `test_bot.py` - Simple test script
- `.env.example` - Environment variable template
- `.env.local` - Your actual environment variables (not tracked by git)

## Dependencies

- `python-telegram-bot==20.3` - Telegram Bot API wrapper
- `python-dotenv==1.0.0` - Environment variable loading
- `Pillow==10.1.0` - Image processing library for barcode generation
