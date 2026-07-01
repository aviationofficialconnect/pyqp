import os
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==========================
# 1) CONFIGURATION & ENV
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
PUBLIC_BASE_URL = "https://pyqp.onrender.com"

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN missing. Add it in Render Secrets.")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==========================
# 2) KEYBOARDS & MENUS
# ==========================
def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🌐 Visit examairways.com", url="https://examairways.com"),
        InlineKeyboardButton("📱 Join WhatsApp Channels", callback_query_data="menu_whatsapp"),
        InlineKeyboardButton("📸 Follow us on Instagram", callback_query_data="menu_instagram")
    )
    return kb

def whatsapp_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("✈️ Pilot Channel (CPL, ATPL, etc.)", url="https://whatsapp.com/channel/0029Vb7hKkjE50UcPqSkjf0r"),
        InlineKeyboardButton("🔧 AME Channel", url="https://whatsapp.com/channel/0029Vb6j7KoBKfhv5A0yd70R"),
        InlineKeyboardButton("🎙️ RTR Channel", url="https://whatsapp.com/channel/0029Vb8adpWEawdnZyLYdk23"),
        InlineKeyboardButton("⬅️ Back to Main Menu", callback_query_data="menu_main")
    )
    return kb

def instagram_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📸 @examairways", url="https://www.instagram.com/examairways/"),
        InlineKeyboardButton("📝 @dgcaexamquestionpaper", url="https://www.instagram.com/dgcaexamquestionpaper/"),
        InlineKeyboardButton("⬅️ Back to Main Menu", callback_query_data="menu_main")
    )
    return kb

# ==========================
# 3) TEXT TEMPLATES
# ==========================
WELCOME_TEXT = (
    "👋 <b>Welcome to Exam Airways!</b>\n\n"
    "Your ultimate destination for aviation exam preparation. On our website, you will find comprehensive study materials and the <b>latest question papers</b> for:\n\n"
    "• 👨‍✈️ <b>Pilot Exams</b> (CPL, ATPL, RTR, etc.)\n"
    "• 🔧 <b>AME Modules</b>\n\n"
    "Click the button below to explore our premium notes and question banks!"
)

WHATSAPP_TEXT = (
    "📢 <b>Join our WhatsApp Channels!</b>\n\n"
    "Get access to <b>free materials</b>, instant exam updates, and important alerts directly on your phone. Select your stream below:"
)

INSTAGRAM_TEXT = (
    "📸 <b>Stay connected on Instagram!</b>\n\n"
    "Follow our official handles for regular updates, exam patterns, and study tips:"
)

# ==========================
# 4) BOT HANDLERS
# ==========================
@bot.message_handler(commands=["start", "help"])
def cmd_start(message):
    bot.send_message(
        message.chat.id, 
        WELCOME_TEXT, 
        reply_markup=main_menu(), 
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("menu_"))
def handle_menus(call):
    bot.answer_callback_query(call.id)
    
    if call.data == "menu_main":
        bot.edit_message_text(
            WELCOME_TEXT, call.message.chat.id, call.message.message_id, 
            reply_markup=main_menu(), disable_web_page_preview=True
        )
    elif call.data == "menu_whatsapp":
        bot.edit_message_text(
            WHATSAPP_TEXT, call.message.chat.id, call.message.message_id, 
            reply_markup=whatsapp_menu(), disable_web_page_preview=True
        )
    elif call.data == "menu_instagram":
        bot.edit_message_text(
            INSTAGRAM_TEXT, call.message.chat.id, call.message.message_id, 
            reply_markup=instagram_menu(), disable_web_page_preview=True
        )

# ==========================
# 5) FLASK SERVER FOR WEBHOOK
# ==========================
app = Flask(__name__)

@app.get("/")
def home():
    return "Bot is running!", 200

@app.post(f"/telegram/{BOT_TOKEN}")
def telegram_webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

# ==========================
# 6) EXECUTION RUNNER
# ==========================
if __name__ == "__main__":
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{PUBLIC_BASE_URL}/telegram/{BOT_TOKEN}")
    except Exception as e:
        print(f"Error setting webhook: {e}")
        
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
