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


# Persistent Footer Buttons (Always shown at the bottom)
def get_footer_buttons():
    return [
        [
            InlineKeyboardButton(
                "🌐 Main Website", url="https://examairways.com/"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 WhatsApp Channel",
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
            InlineKeyboardButton("🛠️ AME", callback_data="stream_ame"),
            InlineKeyboardButton("✈️ PILOT", callback_data="stream_pilot"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "WELCOME TO EXAMAIRWAYS.COM 🛫\n\n"
        "Please select your stream to get started:"
    )

    if update.message:
        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup, parse_mode="Markdown"
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text, reply_markup=reply_markup, parse_mode="Markdown"
        )


# Callback Handler for Button Clicks
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- STEP 1: Stream Selection (AME or Pilot) ---
    if data in ["stream_ame", "stream_pilot"]:
        stream = "AME" if data == "stream_ame" else "PILOT"
        context.user_data["stream"] = stream  # Save choice in context

        keyboard = [
            [InlineKeyboardButton("🇮🇳 DGCA", callback_data="authority_dgca")],
            [
                InlineKeyboardButton(
                    "🇪🇺 EASA (Coming Soon)", callback_data="coming_soon"
                )
            ],
            [
                InlineKeyboardButton(
                    "🇺🇸 FAA (Coming Soon)", callback_data="coming_soon"
                )
            ],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Selected Stream: **{stream}**\n\nSelect the Aviation Authority:",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    # --- STEP 2: Handle 'Coming Soon' Buttons ---
    elif data == "coming_soon":
        stream = context.user_data.get("stream", "Your Stream")
        keyboard = [
            [InlineKeyboardButton("🇮🇳 Select DGCA Instead", callback_data="authority_dgca")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            text=f"🚀 **Coming Soon!**\n\nThis authority section is currently under development. Please check back later or choose DGCA.",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    # --- STEP 3: DGCA Selected -> Show Options ---
    elif data == "authority_dgca":
        stream = context.user_data.get("stream", "PILOT")

        keyboard = [
            [
                InlineKeyboardButton(
                    "📄 Raw PYQ Papers & Study Materials",
                    callback_data="opt_pyq",
                )
            ]
        ]

        # Show Video Lectures and E-Books ONLY for PILOT
        if stream == "PILOT":
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "🎥 Course Video Lectures with Study Materials",
                        callback_data="opt_videos",
                    )
                ]
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "📚 E-Books",
                        callback_data="opt_ebooks",
                    )
                ]
            )

        # Always include Just Exploring & Back button
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔍 Just Exploring",
                    callback_data="opt_exploring",
                )
            ]
        )
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")])

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=f"Selected: **{stream} > DGCA**\n\nWhat are you looking for?",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    # --- STEP 4: Option Deliveries ---
    elif data in ["opt_pyq", "opt_exploring"]:
        keyboard = [
            [
                InlineKeyboardButton(
                    "📖 Access Previous Year Question Papers",
                    url="https://examairways.com/previous-year-question-paper/",
                )
            ]
        ] + get_footer_buttons()

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=(
                "Here is your direct access link:\n\n"
                "------------------------------------\n"
                "❓ *If you have any query, feel free to visit our main website or reach out via email below.*"
            ),
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    elif data == "opt_videos":
        keyboard = [
            [
                InlineKeyboardButton(
                    "🎓 Pilot ATPL Course & Video Lectures",
                    url="https://examairways.com/2215-2/",
                )
            ]
        ] + get_footer_buttons()

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=(
                "Here is your ATPL Course & Video Lecture access link:\n\n"
                "------------------------------------\n"
                "❓ *If you have any query, feel free to visit our main website or reach out via email below.*"
            ),
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    elif data == "opt_ebooks":
        keyboard = [
            [
                InlineKeyboardButton(
                    "📚 Access Pilot E-Books",
                    url="https://examairways.com/2173-2/",
                )
            ]
        ] + get_footer_buttons()

        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            text=(
                "Here is your E-Books access link:\n\n"
                "------------------------------------\n"
                "❓ *If you have any query, feel free to visit our main website or reach out via email below.*"
            ),
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    # Restart flow
    elif data == "restart":
        await start(update, context)


def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start polling
    application.run_polling()


if __name__ == "__main__":
    main()
