import os
import logging
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# 1. Web server to satisfy Render's port check and keep bot alive 24/7
app = Flask(__name__)

@app.route("/")
def home():
    return "ExamAirways Telegram Bot is Live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Footer buttons always shown at the bottom
def get_footer_buttons():
    return [
        [InlineKeyboardButton("🌐 Main Website", url="https://examairways.com/")],
        [
            InlineKeyboardButton(
                "📢 Join WhatsApp Channel",
                url="https://whatsapp.com/channel/0029VbDBVyXJP212QuSRXb3f",
            )
        ],
        [InlineKeyboardButton("✉️ Email Us", url="mailto:examairways@gmail.com")],
        [InlineKeyboardButton("❓ FAQs & Support", callback_data="show_faqs")],
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🛠️ AME", callback_data="stream_ame"),
            InlineKeyboardButton("✈️ PILOT", callback_data="stream_pilot"),
        ]
    ] + get_footer_buttons()

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


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    # Step 1: Stream Selection
    if data in ["stream_ame", "stream_pilot"]:
        stream = "AME" if data == "stream_ame" else "PILOT"
        context.user_data["stream"] = stream

        keyboard = [
            [InlineKeyboardButton("🇮🇳 DGCA", callback_data="authority_dgca")],
            [InlineKeyboardButton("🇪🇺 EASA (Coming Soon)", callback_data="coming_soon")],
            [InlineKeyboardButton("🇺🇸 FAA (Coming Soon)", callback_data="coming_soon")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text=f"Selected Stream: **{stream}**\n\nSelect the Aviation Authority:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Step 2: Coming Soon Handler
    elif data == "coming_soon":
        keyboard = [
            [InlineKeyboardButton("🇮🇳 Select DGCA Instead", callback_data="authority_dgca")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text="🚀 **Coming Soon!**\n\nThis authority section is under development. Please choose DGCA.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Step 3: DGCA Main Menu
    elif data == "authority_dgca":
        stream = context.user_data.get("stream", "PILOT")

        keyboard = [
            [InlineKeyboardButton("📄 Raw PYQs & Study Materials", callback_data="opt_raw_materials")]
        ]

        if stream == "PILOT":
            keyboard.append([InlineKeyboardButton("🎥 Course Video Lectures", callback_data="opt_videos")])
            keyboard.append([InlineKeyboardButton("📚 E-Books", callback_data="opt_ebooks_menu")])

        keyboard.append([InlineKeyboardButton("🔍 Just Exploring", callback_data="opt_exploring")])
        keyboard.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")])
        keyboard.extend(get_footer_buttons())

        await query.edit_message_text(
            text=f"Selected: **{stream} > DGCA**\n\nWhat are you looking for?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Step 4A: Raw Materials
    elif data == "opt_raw_materials":
        stream = context.user_data.get("stream", "PILOT")

        if stream == "PILOT":
            keyboard = [
                [InlineKeyboardButton("🌤️ Met", url="https://cosmofeed.com/vig/65ff2831cf68d10013420bf5")],
                [InlineKeyboardButton("📜 Reg", url="https://cosmofeed.com/vig/67bc91903acba90014c0ed18")],
                [InlineKeyboardButton("⚙️ Tech Gen", url="https://cosmofeed.com/vig/67bdc90e2249ac0013e3c0c8")],
                [InlineKeyboardButton("🧭 Nav", url="https://cosmofeed.com/vig/67bc9211da42c2001319d743")],
                [InlineKeyboardButton("🌟 All in One Bundle", url="https://cosmofeed.com/vig/67bc9211da42c2001319d743")],
            ]
        else:  # AME Modules
            keyboard = [
                [InlineKeyboardButton("Module 3", url="https://cosmofeed.com/vig/68b1e3a410b85b0013ee7000")],
                [InlineKeyboardButton("Module 4", url="https://cosmofeed.com/vig/6885192563dd880013c871ec")],
                [InlineKeyboardButton("Module 5", url="https://cosmofeed.com/vig/68b1e60d5894b900131b389b")],
                [InlineKeyboardButton("Module 6", url="https://cosmofeed.com/vig/68b1e64f8358bd00136cc2d5")],
                [InlineKeyboardButton("Module 7", url="https://cosmofeed.com/vig/68b1e687048157001329f0e1")],
                [InlineKeyboardButton("Module 8", url="https://cosmofeed.com/vig/68b1e6ba048157001329f3cc")],
                [InlineKeyboardButton("Module 9", url="https://cosmofeed.com/vig/68b1e6f110b85b0013eea4c4")],
                [InlineKeyboardButton("Module 10", url="https://cosmofeed.com/vig/68b1e7388358bd00136ccdfb")],
                [InlineKeyboardButton("Module 11", url="https://cosmofeed.com/vig/68b1e7798358bd00136cd159")],
                [InlineKeyboardButton("Module 12", url="https://cosmofeed.com/vig/68b1e7a9048157001329ffb0")],
                [InlineKeyboardButton("Module 13", url="https://cosmofeed.com/vig/68b1e7d910b85b0013eeb0cd")],
                [InlineKeyboardButton("Module 14", url="https://cosmofeed.com/vig/68b1e80304815700132a04cd")],
                [InlineKeyboardButton("Module 15", url="https://cosmofeed.com/vig/68b1e83410b85b0013eeb56a")],
                [InlineKeyboardButton("Module 17", url="https://cosmofeed.com/vig/68b1e85b04815700132a096c")],
            ]

        keyboard.append([InlineKeyboardButton("🔙 Back to DGCA Menu", callback_data="authority_dgca")])
        keyboard.extend(get_footer_buttons())

        await query.edit_message_text(
            text=f"📚 **{stream} Raw Study Materials & Groups:**\nSelect an option below to access:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Step 4B: Pilot E-Books Subject Selection
    elif data == "opt_ebooks_menu":
        keyboard = [
            [InlineKeyboardButton("⚙️ Technical General", callback_data="eb_tech_gen")],
            [InlineKeyboardButton("🌤️ Aviation Meteorology", callback_data="eb_met")],
            [InlineKeyboardButton("🧭 Air Navigation", callback_data="eb_nav")],
            [InlineKeyboardButton("📜 Air Regulation", callback_data="eb_reg")],
            [InlineKeyboardButton("📻 RTR 1", callback_data="eb_rtr")],
            [InlineKeyboardButton("🔙 Back to DGCA Menu", callback_data="authority_dgca")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text="📚 **Pilot E-Books & Question Papers**\n\nSelect a subject to view papers:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Step 4C: Shortened Button Titles (Prevents Telegram Crash)
    elif data.startswith("eb_"):
        keyboard = []
        if data == "eb_tech_gen":
            keyboard = [
                [InlineKeyboardButton("Tech Gen Regular Session 01 (2026)", url="https://superprofile.bio/vp/technical-general-regular-seasons-1-2026")],
                [InlineKeyboardButton("Tech Gen Regular Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-technical-general-regular-session-02-2026-")],
                [InlineKeyboardButton("Tech Gen OLODE Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-technical-general-olode-session-02-2026-")],
            ]
        elif data == "eb_met":
            keyboard = [
                [InlineKeyboardButton("Aviation Met Regular Session 01 (2026)", url="https://superprofile.bio/vp/dgca-aviation-metrology-regular-session-01-2026")],
                [InlineKeyboardButton("Meteorology Regular Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-meteorology-regular-session-02-2026-")],
                [InlineKeyboardButton("Meteorology OLODE Session 01 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-meteorology-olode-session-01-2026")],
                [InlineKeyboardButton("Meteorology OLODE Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-meteorology-olode-session-02-2026")],
                [InlineKeyboardButton("Meteorology OLODE Session 03 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-meteorology-olode-session-03-2026")],
                [InlineKeyboardButton("Meteorology OLODE Session 04 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-meteorology-olode-session-04-2026")],
                [InlineKeyboardButton("Meteorology OLODE Session 05 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-meteorology-olode-session-05-2026")],
            ]
        elif data == "eb_nav":
            keyboard = [
                [InlineKeyboardButton("Air Nav Regular Session 01 (2026)", url="https://superprofile.bio/vp/dgca-air-navigation-regular-session-01-2026")],
                [InlineKeyboardButton("Air Nav Regular Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-navigation-regular-session-02-2026-")],
                [InlineKeyboardButton("Air Nav Questions – 22 Jan OLODE 01", url="https://superprofile.bio/vp/dgca-navigation-questions-–-22-january-2026---olode-session-01-2026")],
                [InlineKeyboardButton("Air Nav OLODE Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-navigation-olode-session-02-2026")],
                [InlineKeyboardButton("Air Nav OLODE Session 03 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-navigation-olode-session-03-2026-812")],
                [InlineKeyboardButton("Air Nav OLODE Session 04 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-navigation-olode-session-04-2026")],
                [InlineKeyboardButton("Air Nav OLODE Session 05 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-navigation-olode-session-05-2026")],
            ]
        elif data == "eb_reg":
            keyboard = [
                [InlineKeyboardButton("Air Reg Regular Session 01 (2026)", url="https://superprofile.bio/vp/dgca-air-regulation-regular-session-01-2026")],
                [InlineKeyboardButton("Air Reg Regular Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-regulation-regular-session-02-2026-")],
                [InlineKeyboardButton("Air Reg OLODE Session 01 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-regulation-olode-session-01-2026")],
                [InlineKeyboardButton("Air Reg OLODE Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-regulations-olode-session-02-2026")],
                [InlineKeyboardButton("Air Reg OLODE Session 03 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-regulations-olode-session-03-2026")],
                [InlineKeyboardButton("Air Reg OLODE Session 04 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-regulations-olode-session-04-2026")],
                [InlineKeyboardButton("Air Reg OLODE Session 05 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-air-regulations-olode-session-05-2026")],
            ]
        elif data == "eb_rtr":
            keyboard = [
                [InlineKeyboardButton("RTR 1 Regular Session 02 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-rtr-1-regular-session-02-2026")],
                [InlineKeyboardButton("RTR 1 OLODE Session 03 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-rtr-1-olode-session-03-2026")],
                [InlineKeyboardButton("RTR 1 OLODE Session 04 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-rtr-1-olode-session-04-2026")],
                [InlineKeyboardButton("RTR 1 OLODE Session 05 (2026)", url="https://superprofile.bio/vp/dgca-question-paper-rtr-1-olode-session-05-2026")],
            ]

        keyboard.append([InlineKeyboardButton("🔙 Back to E-Book Subjects", callback_data="opt_ebooks_menu")])
        keyboard.extend(get_footer_buttons())

        await query.edit_message_text(
            text="📖 **Select your desired paper / e-book to access:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Videos / ATPL Course
    elif data == "opt_videos":
        keyboard = [
            [InlineKeyboardButton("🎓 Pilot ATPL Course & Video Lectures", url="https://examairways.com/2215-2/")],
            [InlineKeyboardButton("🔙 Back to DGCA Menu", callback_data="authority_dgca")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text="Here is your ATPL Course & Video Lecture access link:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # Just Exploring Option
    elif data == "opt_exploring":
        keyboard = [
            [InlineKeyboardButton("📖 Previous Year Question Papers", url="https://examairways.com/previous-year-question-paper/")],
            [InlineKeyboardButton("🔙 Back to DGCA Menu", callback_data="authority_dgca")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text="Feel free to explore our collection of Previous Year Question Papers below:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    # FAQs Section
    elif data == "show_faqs":
        keyboard = [
            [InlineKeyboardButton("📩 How do I get study material?", callback_data="faq_1")],
            [InlineKeyboardButton("🔒 Is payment secure?", callback_data="faq_2")],
            [InlineKeyboardButton("📦 What is included in subscription?", callback_data="faq_3")],
            [InlineKeyboardButton("📚 Can I access multiple subjects?", callback_data="faq_4")],
            [InlineKeyboardButton("❌ Refund Policy", callback_data="faq_5")],
            [InlineKeyboardButton("💸 How does reselling work?", callback_data="faq_6")],
            [InlineKeyboardButton("🌐 Reselling for other subjects?", callback_data="faq_7")],
            [InlineKeyboardButton("💰 How do I receive commission?", callback_data="faq_8")],
            [InlineKeyboardButton("📞 How to contact support?", callback_data="faq_9")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text="❓ **Frequently Asked Questions (FAQs)**\nSelect a topic below to read details:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data.startswith("faq_"):
        faq_texts = {
            "faq_1": "📩 **How do I get the study material?**\n\nClick on Buy Now, select the subject, and make the payment. After payment, you’ll get secure Telegram channel access.",
            "faq_2": "🔒 **Is the payment secure?**\n\nYes, all payments are processed via 100% secure gateways with SSL encryption.",
            "faq_3": "📦 **What is included in the subscription?**\n\nYou’ll get Previous Year Papers, Chapter-wise Question Banks, and Mock Test Papers. Content is updated regularly.",
            "faq_4": "📚 **Can I access multiple subjects?**\n\nYes, you can subscribe to more than one subject/module at the same time.",
            "faq_5": "❌ **Refund Policy**\n\nSince this is digital content with instant access, refunds are not possible once material is delivered.",
            "faq_6": "💸 **How does reselling work?**\n\nRight now, only the Pilot 4-in-1 Bundle has reselling enabled. On its page, click Resell, enter your mobile number, and generate a referral link. You’ll get 10% commission when someone buys via your link.",
            "faq_7": "🌐 **Will reselling be available for other subjects?**\n\nYes, we plan to expand the referral program to all Pilot subjects and AME modules soon. For now, it’s limited to the Pilot 4-in-1 Bundle.",
            "faq_8": "💰 **How do I receive commission?**\n\nYour earnings (10% of the bundle fee) are credited to your Cosmofeed registered account/UPI after successful payment by the buyer.",
            "faq_9": "📞 **How can I contact you?**\n\nEmail us anytime at: examairways@gmail.com",
        }

        ans = faq_texts.get(data, "FAQ details not found.")
        keyboard = [
            [InlineKeyboardButton("🔙 Back to FAQs List", callback_data="show_faqs")],
            [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="restart")],
        ] + get_footer_buttons()

        await query.edit_message_text(
            text=f"{ans}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "restart":
        await start(update, context)


def main():
    if not BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set!")

    # Start Flask Web Server on background thread so Render detects a running port
    Thread(target=run_flask, daemon=True).start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    application.run_polling()


if __name__ == "__main__":
    main()
