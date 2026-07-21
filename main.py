import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Fetch Token from Environment Variable / Secrets
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")


# --- HELPER FUNCTIONS FOR MENUS ---

def get_footer_text() -> str:
    return (
        "\n\n------------------------------------\n"
        "📩 **If you have any queries, feel free to reach out:**\n"
        "🌐 **Main Website:** [examairways.com](https://examairways.com/)\n"
        "📚 **Previous Year Papers & Groups:** [Click Here](https://examairways.com/previous-year-question-paper/)\n"
        "📧 **Email Support:** examairways@gmail.com"
    )

def get_footer_buttons() -> list[list[InlineKeyboardButton]]:
    return [
        [InlineKeyboardButton("🌐 Visit Main Website", url="https://examairways.com/")],
        [InlineKeyboardButton("📚 Group Details & Previous Year Papers", url="https://examairways.com/previous-year-question-paper/")],
        [InlineKeyboardButton("📧 Contact Support via Email", url="mailto:examairways@gmail.com")]
    ]


# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initial /start command handler."""
    text = (
        "Welcome to **Exam Airways**! ✈️\n\n"
        "Please select your category to get started:"
    )
    keyboard = [
        [
            InlineKeyboardButton("Pilot", callback_data="role_pilot"),
            InlineKeyboardButton("AME (Aircraft Maintenance)", callback_data="role_ame"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")


async def main_options_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, role: str):
    """Shows Main Menu options after selecting Pilot or AME."""
    query = update.callback_query
    await query.answer()

    role_title = "Pilot" if role == "pilot" else "AME"
    text = f"Selected Stream: **{role_title}**\n\nChoose an option below:"

    keyboard = [
        [InlineKeyboardButton("📖 Get Access to Latest Study Materials", callback_data=f"materials_{role}")],
        [InlineKeyboardButton("💬 Join Free Community", url="https://examairways.com/previous-year-question-paper/")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_over")]
    ]
    keyboard.extend(get_footer_buttons())

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text + get_footer_text(), reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)


async def show_premium_groups(update: Update, context: ContextTypes.DEFAULT_TYPE, role: str):
    """Displays subject/module premium links along with the FAQ option."""
    query = update.callback_query
    await query.answer()

    if role == "pilot":
        text = "🎯 **Premium Groups for Pilot Exams:**\nChoose your subject below to enroll:"
        keyboard = [
            [InlineKeyboardButton("Meteorology (Met)", url="https://cosmofeed.com/vig/65ff2831cf68d10013420bf5")],
            [InlineKeyboardButton("Air Regulations (Reg)", url="https://cosmofeed.com/vig/67bc91903acba90014c0ed18")],
            [InlineKeyboardButton("Technical General", url="https://cosmofeed.com/vig/67bdc90e2249ac0013e3c0c8")],
            [InlineKeyboardButton("Air Navigation", url="https://cosmofeed.com/vig/67bc9211da42c2001319d743")],
            [InlineKeyboardButton("⭐ All-in-One Pilot Bundle", url="https://cosmofeed.com/vig/67bc9211da42c2001319d743")],
            [InlineKeyboardButton("❓ Frequently Asked Questions (FAQs)", callback_data="show_faqs_pilot")],
            [InlineKeyboardButton("🔙 Back", callback_data="role_pilot")]
        ]
    else:  # AME
        text = "🛠️ **Premium Groups for AME Modules:**\nChoose your module below to enroll:"
        keyboard = [
            [InlineKeyboardButton("Module 3", url="https://cosmofeed.com/vig/68b1e3a410b85b0013ee7000"), InlineKeyboardButton("Module 4", url="https://cosmofeed.com/vig/6885192563dd880013c871ec")],
            [InlineKeyboardButton("Module 5", url="https://cosmofeed.com/vig/68b1e60d5894b900131b389b"), InlineKeyboardButton("Module 6", url="https://cosmofeed.com/vig/68b1e64f8358bd00136cc2d5")],
            [InlineKeyboardButton("Module 7", url="https://cosmofeed.com/vig/68b1e687048157001329f0e1"), InlineKeyboardButton("Module 8", url="https://cosmofeed.com/vig/68b1e6ba048157001329f3cc")],
            [InlineKeyboardButton("Module 9", url="https://cosmofeed.com/vig/68b1e6f110b85b0013eea4c4"), InlineKeyboardButton("Module 10", url="https://cosmofeed.com/vig/68b1e7388358bd00136ccdfb")],
            [InlineKeyboardButton("Module 11", url="https://cosmofeed.com/vig/68b1e7798358bd00136cd159"), InlineKeyboardButton("Module 12", url="https://cosmofeed.com/vig/68b1e7a9048157001329ffb0")],
            [InlineKeyboardButton("Module 13", url="https://cosmofeed.com/vig/68b1e7d910b85b0013eeb0cd"), InlineKeyboardButton("Module 14", url="https://cosmofeed.com/vig/68b1e80304815700132a04cd")],
            [InlineKeyboardButton("Module 15", url="https://cosmofeed.com/vig/68b1e83410b85b0013eeb56a"), InlineKeyboardButton("Module 17", url="https://cosmofeed.com/vig/68b1e85b04815700132a096c")],
            [InlineKeyboardButton("❓ Frequently Asked Questions (FAQs)", callback_data="show_faqs_ame")],
            [InlineKeyboardButton("🔙 Back", callback_data="role_ame")]
        ]

    keyboard.extend(get_footer_buttons())
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text + get_footer_text(), reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)


async def show_faqs(update: Update, context: ContextTypes.DEFAULT_TYPE, prev_role: str):
    """Displays full FAQ section with cleaned up grammar."""
    query = update.callback_query
    await query.answer()

    faq_text = (
        "❓ **Frequently Asked Questions (FAQs)**\n\n"
        "📌 **How do I get the study material?**\n"
        "Click on 'Buy Now', select the subject, and complete the payment. Upon completion, you will instantly gain access to the private Telegram channel.\n\n"
        "🔒 **Is the payment secure?**\n"
        "Yes, all payments are processed through 100% secure payment gateways with SSL encryption.\n\n"
        "📦 **What is included in the subscription?**\n"
        "You get Previous Year Papers, Chapter-wise Question Banks, and Mock Test Papers. Content is updated regularly.\n\n"
        "📚 **Can I access multiple subjects?**\n"
        "Yes, you can subscribe to multiple subjects or modules simultaneously.\n\n"
        "💳 **Refund Policy**\n"
        "Since this is instant-access digital content, refunds are not possible once access is granted.\n\n"
        "🤝 **How does reselling work?**\n"
        "Currently, reselling is active for the **Pilot 4-in-1 Bundle**. Click 'Resell' on the payment page, enter your phone number, and generate a referral link. You earn a 10% commission on every sale made via your link!\n\n"
        "🚀 **Will reselling be available for other subjects?**\n"
        "Yes! We plan to expand the referral program to all Pilot subjects and AME modules soon.\n\n"
        "💰 **How do I receive commissions?**\n"
        "Your earnings (10% of the bundle fee) are directly credited to your Cosmofeed registered account/UPI after a successful buyer transaction.\n\n"
        "📩 **Contact & Support:** examairways@gmail.com\n"
        "📸 **Follow us on Instagram**\n\n"
        "*This is DGCA previous year Question paper*\n"
        "© 2026 examairways.com • Built with GeneratePress"
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Back to Group Links", callback_data=f"materials_{prev_role}")],
        [InlineKeyboardButton("🏠 Back to Start", callback_data="start_over")]
    ]
    keyboard.extend(get_footer_buttons())

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(faq_text + get_footer_text(), reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)


async def button_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Router for all inline query button clicks."""
    query = update.callback_query
    data = query.data

    if data == "start_over":
        await start(update, context)
    elif data in ["role_pilot", "role_ame"]:
        role = "pilot" if data == "role_pilot" else "ame"
        await main_options_menu(update, context, role)
    elif data in ["materials_pilot", "materials_ame"]:
        role = "pilot" if data == "materials_pilot" else "ame"
        await show_premium_groups(update, context, role)
    elif data in ["show_faqs_pilot", "show_faqs_ame"]:
        role = "pilot" if data == "show_faqs_pilot" else "ame"
        await show_faqs(update, context, role)


def main():
    if not TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN environment variable! Set it in your secrets.")

    app = Application.builder().token(TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_router))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
