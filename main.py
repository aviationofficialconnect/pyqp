import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Fetch Bot Token securely from environment variables
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Common persistent footer buttons (Always shown at the bottom)
def get_footer_keyboard():
    return [
        [
            InlineKeyboardButton(
                "🌐 Main Website", url="https://examairways.com/"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Join WhatsApp Channel",
                url="https://whatsapp.com/channel/0029VbDBVyXJP212QuSRXb3f",
            )
        ],
        [
            InlineKeyboardButton(
                "✉️ Support Email", url="mailto:examairways@gmail.com"
            )
        ],
    ]

# /start Command Handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🛠️ AME", callback_data="category_ame"),
            InlineKeyboardButton("✈️ Pilot", callback_data="category_pilot"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "Welcome to **ExamAirways**! 🛫\n\n"
        "Please select your course stream to get started:"
    )
    
    await update.message.reply_text(
        welcome_text, reply_markup=reply_markup, parse_mode="Markdown"
    )

# Callback Handler for Category Selection (AME or Pilot)
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    selected_category = "AME" if query.data == "category_ame" else "Pilot"

    # Category-specific options + Footer buttons
    keyboard = [
        [
            InlineKeyboardButton(
                "📚 Get Access to Latest Study Materials",
                url="https://examairways.com/",
            )
        ],
        [
            InlineKeyboardButton(
                "💬 Join Free WhatsApp Community",
                url="https://whatsapp.com/channel/0029VbDBVyXJP212QuSRXb3f",
            )
        ],
    ] + get_footer_keyboard()

    reply_markup = InlineKeyboardMarkup(keyboard)

    message_text = (
        f"You selected: **{selected_category}**\n\n"
        "Choose an option below to access study resources or connect with us.\n\n"
        "------------------------------------\n"
        "❓ **If you have any queries, feel free to visit our main website or reach out via email below.**"
    )

    await query.edit_message_text(
        text=message_text, reply_markup=reply_markup, parse_mode="Markdown"
    )

def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(category_handler, pattern="^category_"))

    # Start the Bot
    application.run_polling()

if __name__ == "__main__":
    main()
