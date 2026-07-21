import os
from telebot import TeleBot, types

# Fetch Token from Render Environment Secrets
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
bot = TeleBot(TOKEN)

# --- HELPER FOOTER ---
FOOTER_TEXT = (
    "\n\n------------------------------------\n"
    "📩 **If you have any queries, feel free to reach out:**\n"
    "🌐 **Main Website:** [examairways.com](https://examairways.com/)\n"
    "📚 **Previous Year Papers & Groups:** [Click Here](https://examairways.com/previous-year-question-paper/)\n"
    "📧 **Email Support:** examairways@gmail.com"
)

def add_footer_buttons(markup):
    markup.add(types.InlineKeyboardButton("🌐 Visit Main Website", url="https://examairways.com/"))
    markup.add(types.InlineKeyboardButton("📚 Group Details & Previous Year Papers", url="https://examairways.com/previous-year-question-paper/"))
    markup.add(types.InlineKeyboardButton("📧 Contact Support via Email", url="mailto:examairways@gmail.com"))
    return markup


# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    btn_pilot = types.InlineKeyboardButton("Pilot", callback_data="role_pilot")
    btn_ame = types.InlineKeyboardButton("AME (Aircraft Maintenance)", callback_data="role_ame")
    markup.row(btn_pilot, btn_ame)
    
    bot.send_message(
        message.chat.id,
        "Welcome to **Exam Airways**! ✈️\n\nPlease select your category to get started:",
        parse_mode="Markdown",
        reply_markup=markup
    )


# --- CALLBACK ROUTER ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if call.data == "start_over":
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Pilot", callback_data="role_pilot"),
            types.InlineKeyboardButton("AME (Aircraft Maintenance)", callback_data="role_ame")
        )
        bot.edit_message_text(
            "Welcome to **Exam Airways**! ✈️\n\nPlease select your category to get started:",
            chat_id, message_id, parse_mode="Markdown", reply_markup=markup
        )

    elif call.data in ["role_pilot", "role_ame"]:
        role = "pilot" if call.data == "role_pilot" else "ame"
        role_title = "Pilot" if role == "pilot" else "AME"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📖 Get Access to Latest Study Materials", callback_data=f"materials_{role}"))
        markup.add(types.InlineKeyboardButton("💬 Join Free Community", url="https://examairways.com/previous-year-question-paper/"))
        markup.add(types.InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_over"))
        markup = add_footer_buttons(markup)

        bot.edit_message_text(
            f"Selected Stream: **{role_title}**\n\nChoose an option below:" + FOOTER_TEXT,
            chat_id, message_id, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True
        )

    elif call.data == "materials_pilot":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Meteorology (Met)", url="https://cosmofeed.com/vig/65ff2831cf68d10013420bf5"))
        markup.add(types.InlineKeyboardButton("Air Regulations (Reg)", url="https://cosmofeed.com/vig/67bc91903acba90014c0ed18"))
        markup.add(types.InlineKeyboardButton("Technical General", url="https://cosmofeed.com/vig/67bdc90e2249ac0013e3c0c8"))
        markup.add(types.InlineKeyboardButton("Air Navigation", url="https://cosmofeed.com/vig/67bc9211da42c2001319d743"))
        markup.add(types.InlineKeyboardButton("⭐ All-in-One Pilot Bundle", url="https://cosmofeed.com/vig/67bc9211da42c2001319d743"))
        markup.add(types.InlineKeyboardButton("❓ Frequently Asked Questions (FAQs)", callback_data="show_faqs_pilot"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="role_pilot"))
        markup = add_footer_buttons(markup)

        bot.edit_message_text(
            "🎯 **Premium Groups for Pilot Exams:**\nChoose your subject below to enroll:" + FOOTER_TEXT,
            chat_id, message_id, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True
        )

    elif call.data == "materials_ame":
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Module 3", url="https://cosmofeed.com/vig/68b1e3a410b85b0013ee7000"), types.InlineKeyboardButton("Module 4", url="https://cosmofeed.com/vig/6885192563dd880013c871ec"))
        markup.row(types.InlineKeyboardButton("Module 5", url="https://cosmofeed.com/vig/68b1e60d5894b900131b389b"), types.InlineKeyboardButton("Module 6", url="https://cosmofeed.com/vig/68b1e64f8358bd00136cc2d5"))
        markup.row(types.InlineKeyboardButton("Module 7", url="https://cosmofeed.com/vig/68b1e687048157001329f0e1"), types.InlineKeyboardButton("Module 8", url="https://cosmofeed.com/vig/68b1e6ba048157001329f3cc"))
        markup.row(types.InlineKeyboardButton("Module 9", url="https://cosmofeed.com/vig/68b1e6f110b85b0013eea4c4"), types.InlineKeyboardButton("Module 10", url="https://cosmofeed.com/vig/68b1e7388358bd00136ccdfb"))
        markup.row(types.InlineKeyboardButton("Module 11", url="https://cosmofeed.com/vig/68b1e7798358bd00136cd159"), types.InlineKeyboardButton("Module 12", url="https://cosmofeed.com/vig/68b1e7a9048157001329ffb0"))
        markup.row(types.InlineKeyboardButton("Module 13", url="https://cosmofeed.com/vig/68b1e7d910b85b0013eeb0cd"), types.InlineKeyboardButton("Module 14", url="https://cosmofeed.com/vig/68b1e80304815700132a04cd"))
        markup.row(types.InlineKeyboardButton("Module 15", url="https://cosmofeed.com/vig/68b1e83410b85b0013eeb56a"), types.InlineKeyboardButton("Module 17", url="https://cosmofeed.com/vig/68b1e85b04815700132a096c"))
        markup.add(types.InlineKeyboardButton("❓ Frequently Asked Questions (FAQs)", callback_data="show_faqs_ame"))
        markup.add(types.InlineKeyboardButton("🔙 Back", callback_data="role_ame"))
        markup = add_footer_buttons(markup)

        bot.edit_message_text(
            "🛠️ **Premium Groups for AME Modules:**\nChoose your module below to enroll:" + FOOTER_TEXT,
            chat_id, message_id, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True
        )

    elif call.data in ["show_faqs_pilot", "show_faqs_ame"]:
        prev_role = "pilot" if call.data == "show_faqs_pilot" else "ame"
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
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 Back to Group Links", callback_data=f"materials_{prev_role}"))
        markup.add(types.InlineKeyboardButton("🏠 Back to Start", callback_data="start_over"))
        markup = add_footer_buttons(markup)

        bot.edit_message_text(
            faq_text + FOOTER_TEXT, chat_id, message_id, parse_mode="Markdown", reply_markup=markup, disable_web_page_preview=True
        )


if __name__ == "__main__":
    print("Bot is polling...")
    bot.infinity_polling()
