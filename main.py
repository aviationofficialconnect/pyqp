import os
import hmac
import hashlib
import razorpay
import telebot
from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Razorpay webhook secret

bot = telebot.TeleBot(BOT_TOKEN)
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
app = Flask(__name__)

# Test subject for you only (₹1)
SUBJECTS = {
    "Module 10": {"price": 100, "channel": "-1002222222222"},   # Example Telegram channel ID
    "All 4 in 1": {"price": 14900, "channel": "-1003333333333"}, # ₹149.00
    "Test Subject": {"price": 100, "channel": "-1004444444444"}, # ₹1.00
}

user_access = {}
scheduler = BackgroundScheduler()
scheduler.start()

# ---------------- FAQs ----------------
FAQs = """
❓ **FAQs**

**How do I access the content?**  
After payment, you’ll receive Telegram channel access details via email/SMS within 15 minutes.

**Is the payment secure?**  
We use 100% secure payment gateways with SSL encryption.

**Will I get updates?**  
Yes ✅, we regularly update content in the Telegram channels.

**Refund Policy**  
⚠️ Digital content cannot be refunded once accessed.

📧 For queries or issues: examairways@gmail.com
"""

# ---------------- Flask Routes ----------------
@app.route('/payment_callback', methods=['POST'])
def payment_callback():
    payload = request.data
    signature = request.headers.get("X-Razorpay-Signature")

    # Verify webhook signature
    expected_signature = hmac.new(
        bytes(WEBHOOK_SECRET, "utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        abort(400, "Invalid signature")

    data = request.json
    event = data.get("event")

    if event == "payment.captured":
        payment_id = data["payload"]["payment"]["entity"]["id"]
        notes = data["payload"]["payment"]["entity"].get("notes", {})
        user_id = notes.get("user_id")
        subject = notes.get("subject")

        if user_id and subject in SUBJECTS:
            give_access(int(user_id), subject)

    return "OK", 200

# ---------------- Telegram Commands ----------------
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "👋 Welcome to *Exam Airways Bot*!\n\n"
        "📚 Available Subjects:\n"
        "1️⃣ Module 10 – ₹100\n"
        "2️⃣ All 4 in 1 – ₹149\n"
        "3️⃣ Test Subject – ₹1 (for testing only)\n\n"
        "Type the subject name to purchase (e.g., 'Module 10').\n\n"
        "For FAQs, type /faq"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(commands=['faq'])
def faq(message):
    bot.reply_to(message, FAQs, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text in SUBJECTS)
def buy_subject(message):
    subject = message.text
    user_id = message.from_user.id

    order = client.order.create({
        "amount": SUBJECTS[subject]["price"],
        "currency": "INR",
        "payment_capture": "1",
        "notes": {"user_id": str(user_id), "subject": subject}
    })

    payment_link = f"https://rzp.io/i/{order['id']}"
    bot.reply_to(message, f"💳 Pay here to access *{subject}*:\n{payment_link}", parse_mode="Markdown")

# ---------------- Access Control ----------------
def give_access(user_id, subject):
    channel_id = SUBJECTS[subject]["channel"]
    expiry = datetime.now() + timedelta(days=30)

    if subject == "Test Subject":  # Special case
        expiry = datetime.now() + timedelta(minutes=10)

    user_access[(user_id, subject)] = expiry
    bot.send_message(user_id, f"✅ Payment successful!\nYou have been added to *{subject}*.", parse_mode="Markdown")
    try:
        bot.unban_chat_member(channel_id, user_id)  # Add user
    except Exception as e:
        bot.send_message(user_id, f"⚠️ Could not add you automatically. Contact support. Error: {str(e)}")

    scheduler.add_job(remove_access, 'date', run_date=expiry, args=[user_id, subject])

def remove_access(user_id, subject):
    channel_id = SUBJECTS[subject]["channel"]
    try:
        bot.kick_chat_member(channel_id, user_id)
        bot.unban_chat_member(channel_id, user_id)  # Ensure they can rejoin later
    except Exception as e:
        print(f"Error removing user {user_id}: {str(e)}")

# ---------------- Start Flask + Bot ----------------
import threading
def run_bot():
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
