import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone

from flask import Flask, request
import telebot
import razorpay
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from telebot import apihelper as tg_apihelper

# ==========================
# 1) READ SECRETS FROM ENV
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN missing. Add it in Render Secrets.")
if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    raise SystemExit("❌ Razorpay keys missing. Add them in Render Secrets.")

# ==========================
# 2) CHANNEL MAP
# ==========================
CHANNELS = {
    "pilot": {
        "Met": -1001909727391,
        "Reg": -1001847311370,
        "Tech gen": -1002341128726,
        "Nav": -1001893526782,
        "All in One": -1002213153230,   # special price: 149
    },
    "ame": {
        "Module 3": -1002638241867,
        "Module 4": -1002427747376,
        "Module 5": -1002815109827,
        "Module 6": -1002825896960,
        "Module 7": -1002705178906,
        "Module 8": -1002817341522,
        "Module 9": -1002884993111,
        "Module 10": -1002669201096,
        "Module 11": -1002751824894,
        "Module 12": -1002887031500,
        "Module 13": -1002741574944,
        "Module 14": -1002781937799,
        "Module 15": -1002667154098,
        "Module 17": -1002861793286,
        # --- Test subject (₹1) → temporary, for you only ---
        "TEST: Module 10 (10 min)": -1002669201096,
    },
}

# Pricing rules
PRICE_DEFAULT_INR = 49
SPECIAL_PRICES = {
    ("pilot", "All in One"): 149,
    ("ame", "TEST: Module 10 (10 min)"): 1,
}
DAYS_PER_SUB = 30
REMINDER_DAYS_BEFORE = 2  # send reminder X days before expiry

# ==========================
# 3) INIT TELEGRAM & RAZORPAY
# ==========================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Background scheduler (for test auto-remove + reminders/kicks)
scheduler = BackgroundScheduler()

# ==========================
# 4) SQLITE DB
# ==========================
DB_PATH = "subs.db"

def db_connect():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def db_init():
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            stream TEXT NOT NULL,
            subject TEXT NOT NULL,
            channel_id INTEGER NOT NULL,
            paid_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            status TEXT NOT NULL,        -- active | expired
            last_reminder_at TEXT,
            UNIQUE(user_id, subject)
        );"""
    )
    conn.commit()
    conn.close()

def upsert_subscription(user_id: int, username: str, stream: str, subject: str, channel_id: int, extend_days: int = DAYS_PER_SUB):
    now = datetime.now(timezone.utc)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT expires_at FROM subscriptions WHERE user_id=? AND subject=?", (user_id, subject))
    row = cur.fetchone()

    if row:
        current_expiry = datetime.fromisoformat(row[0])
        if current_expiry > now:
            new_expiry = current_expiry + timedelta(days=extend_days)
        else:
            new_expiry = now + timedelta(days=extend_days)
        cur.execute(
            "UPDATE subscriptions SET paid_at=?, expires_at=?, status=?, last_reminder_at=? WHERE user_id=? AND subject=?",
            (now.isoformat(), new_expiry.isoformat(), "active", None, user_id, subject),
        )
    else:
        new_expiry = now + timedelta(days=extend_days)
        cur.execute(
            "INSERT INTO subscriptions (user_id, username, stream, subject, channel_id, paid_at, expires_at, status, last_reminder_at) VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, username, stream, subject, channel_id, now.isoformat(), new_expiry.isoformat(), "active", None),
        )

    conn.commit()
    conn.close()
    return new_expiry

def fetch_due_reminders():
    now = datetime.now(timezone.utc)
    target = now + timedelta(days=REMINDER_DAYS_BEFORE)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id, subject, expires_at FROM subscriptions WHERE status='active' AND (last_reminder_at IS NULL)")
    rows = cur.fetchall()
    conn.close()
    due = []
    for user_id, subject, expires_at in rows:
        exp = datetime.fromisoformat(expires_at)
        if now < exp <= target:
            due.append((user_id, subject, exp))
    return due

def mark_reminded(user_id: int, subject: str):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE subscriptions SET last_reminder_at=? WHERE user_id=? AND subject=?", (datetime.now(timezone.utc).isoformat(), user_id, subject))
    conn.commit()
    conn.close()

def fetch_expired():
    now = datetime.now(timezone.utc)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT user_id, subject, channel_id, expires_at FROM subscriptions WHERE status='active'")
    rows = cur.fetchall()
    conn.close()
    expired = []
    for user_id, subject, channel_id, expires_at in rows:
        if datetime.fromisoformat(expires_at) <= now:
            expired.append((user_id, subject, channel_id))
    return expired

def mark_expired(user_id: int, subject: str):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("UPDATE subscriptions SET status='expired' WHERE user_id=? AND subject=?", (user_id, subject))
    conn.commit()
    conn.close()

# ==========================
# Helpers
# ==========================
def price_for(stream: str, subject: str) -> int:
    return SPECIAL_PRICES.get((stream, subject), PRICE_DEFAULT_INR)

def schedule_kick(user_id: int, channel_id: int, after_seconds: int = 600):
    run_at = datetime.now(timezone.utc) + timedelta(seconds=after_seconds)

    def _kick():
        try:
            bot.ban_chat_member(channel_id, user_id)
            bot.unban_chat_member(channel_id, user_id)  # allow rejoin later if needed
        except Exception as e:
            print("Kick error (test):", e)
        try:
            bot.send_message(user_id, "⏰ Your test access (10 min) has expired. You’ve been removed from the channel.")
        except Exception as e:
            print("Notify user after test expiry error:", e)

    try:
        scheduler.add_job(_kick, "date", run_date=run_at)
    except Exception as e:
        print("Scheduler add_job error:", e)

# ==========================
# 5) MENUS
# ==========================
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Pilot", callback_data="stream:pilot"))
    kb.add(InlineKeyboardButton("AME", callback_data="stream:ame"))
    kb.add(InlineKeyboardButton("FAQ", callback_data="faq"))
    return kb

def subjects_menu(stream: str):
    kb = InlineKeyboardMarkup()
    for subject in CHANNELS[stream].keys():
        kb.add(InlineKeyboardButton(subject, callback_data=f"subject:{stream}:{subject}"))
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back"))
    return kb

# ==========================
# 6) BOT HANDLERS
# ==========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    bot.send_message(message.chat.id, "Select your category:", reply_markup=main_menu())

@bot.callback_query_handler(func=lambda c: c.data == "faq")
def cb_faq(call):
    bot.answer_callback_query(call.id)
    faq_html = (
        "<b>📘 FAQs</b>\n\n"
        "<b>1) How do I access the content?</b>\n"
        "After payment, you’ll receive Telegram channel access details via email/SMS within 15 minutes.\n\n"
        "<b>2) Is the payment secure?</b>\n"
        "We use 100% secure payment gateways with SSL encryption.\n\n"
        "<b>3) Will I get updates?</b>\n"
        "Yes, we regularly update content in the Telegram channels.\n\n"
        "<b>4) Refund Policy</b>\n"
        "Digital content cannot be refunded once accessed.\n\n"
        "<b>5) Have a query or issue?</b>\n"
        "Contact us at <a href='mailto:examairways@gmail.com'>examairways@gmail.com</a>"
    )
    try:
        bot.edit_message_text(
            faq_html,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu(),
            parse_mode="HTML",
            disable_web_page_preview=True,
        )
    except tg_apihelper.ApiTelegramException as e:
        # Ignore harmless "message is not modified" errors
        if "message is not modified" not in str(e):
            raise

@bot.callback_query_handler(func=lambda c: c.data == "back")
def cb_back(call):
    bot.answer_callback_query(call.id)
    try:
        bot.edit_message_text("Select your category:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    except tg_apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise

@bot.callback_query_handler(func=lambda c: c.data.startswith("stream:"))
def cb_stream(call):
    bot.answer_callback_query(call.id)
    stream = call.data.split(":", 1)[1]
    try:
        bot.edit_message_text(
            f"Select subject for <b>{stream.upper()}</b>:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=subjects_menu(stream),
        )
    except tg_apihelper.ApiTelegramException as e:
        if "message is not modified" not in str(e):
            raise

@bot.callback_query_handler(func=lambda c: c.data.startswith("subject:"))
def cb_subject(call):
    bot.answer_callback_query(call.id)
    _, stream, subject = call.data.split(":", 2)

    # Choose price based on subject
    price_inr = price_for(stream, subject)

    try:
        payment = rz_client.payment_link.create({
            "amount": price_inr * 100,  # paise
            "currency": "INR",
            "description": f"Subscription for {subject}",
            "notes": {
                "user_id": call.from_user.id,
                "username": call.from_user.username or "",
                "stream": stream,
                "subject": subject,
            },
            "notify": {"sms": False, "email": False},
            # TODO: replace with your live Render URL once deployed
            "callback_url": "https://your-app.onrender.com",
            "callback_method": "get",
        })
        short_url = payment.get("short_url")

        if subject == "TEST: Module 10 (10 min)":
            info_line = f"Pay ₹{price_inr} for a 10-minute test access to <b>Module 10</b>."
        elif subject == "All in One":
            info_line = f"Pay ₹{price_inr}/month for <b>{subject}</b> (bundle)."
        else:
            info_line = f"Pay ₹{price_inr}/month for <b>{subject}</b>."

        try:
            bot.edit_message_text(
                info_line + "\n\nAfter successful payment, you'll get the channel link automatically.",
                call.message.chat.id,
                call.message.message_id,
            )
        except tg_apihelper.ApiTelegramException as e:
            if "message is not modified" not in str(e):
                raise

        bot.send_message(call.message.chat.id, short_url)

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error creating payment link: {e}")

# ==========================
# 7) FLASK WEB SERVER (Webhook)
# ==========================
app = Flask(__name__)

@app.get("/")
def home():
    return "OK", 200

@app.post("/webhook")
def webhook():
    try:
        payload = request.data.decode("utf-8")
        data = request.get_json(force=True)
        signature = request.headers.get("X-Razorpay-Signature", "")

        # Verify signature if secret is configured
        if RAZORPAY_WEBHOOK_SECRET:
            try:
                razorpay.Utility.verify_webhook_signature(payload, signature, RAZORPAY_WEBHOOK_SECRET)
            except Exception as e:
                print("❌ Invalid webhook signature:", e)
                return "Invalid signature", 400

        event = data.get("event")
        if event == "payment_link.paid":
            pl = data["payload"]["payment_link"]["entity"]
            notes = pl.get("notes", {})
            user_id = int(notes.get("user_id"))
            username = notes.get("username") or ""
            stream = notes.get("stream")
            subject = notes.get("subject")

            channel_id = CHANNELS.get(stream, {}).get(subject)
            if not channel_id:
                print("⚠️ Unknown channel for:", stream, subject)
                return "Unknown channel", 200

            now_utc = datetime.now(timezone.utc)

            # --- Test subject: 10-minute access only, no DB subscription entry ---
            if subject == "TEST: Module 10 (10 min)":
                try:
                    expire_ts = int((now_utc + timedelta(minutes=10)).timestamp())
                    invite = bot.create_chat_invite_link(channel_id, expire_date=expire_ts, member_limit=1)
                    link = invite.invite_link
                except Exception as e:
                    print("Test invite link error:", e)
                    link = None

                # Schedule kick in 10 minutes
                schedule_kick(user_id=user_id, channel_id=channel_id, after_seconds=600)

                # Notify user
                try:
                    msg = (
                        "✅ Test payment received!\n\n"
                        "Access: <b>Module 10 (TEST)</b>\n"
                        "Valid for: <b>10 minutes</b>\n\n"
                        f"Join link: {link if link else 'Please contact support, link generation failed.'}\n\n"
                        "Note: The link works once. If it expires, reply here."
                    )
                    bot.send_message(user_id, msg)
                except Exception as e:
                    print("Send test message error:", e)

                return "OK", 200

            # --- Normal subscription flow (49 or 149 for All in One) ---
            try:
                new_expiry = upsert_subscription(user_id, username, stream, subject, channel_id)
            except Exception as e:
                print("DB upsert error:", e)
                return "OK", 200

            # Create invite link that expires at subscription expiry
            try:
                expire_ts = int(new_expiry.timestamp())
                invite = bot.create_chat_invite_link(channel_id, expire_date=expire_ts, member_limit=1)
                link = invite.invite_link
            except Exception as e:
                print("Invite link error:", e)
                link = None

            # Notify user
            try:
                exp_str = new_expiry.astimezone(timezone(timedelta(hours=5, minutes=30))).strftime("%d-%m-%Y %H:%M IST")
                msg = (
                    f"✅ Payment received!\n\n"
                    f"Access: <b>{subject}</b>\n"
                    f"Valid till: <b>{exp_str}</b>\n\n"
                    f"Join link: {link if link else 'Please contact support, link generation failed.'}\n\n"
                    f"Note: The link works once. If it expires, reply here."
                )
                bot.send_message(user_id, msg)
            except Exception as e:
                print("Send message error:", e)

        else:
            # handle/ignore other events if enabled in Razorpay
            pass

        return "OK", 200

    except Exception as e:
        print("Webhook handler error:", e)
        # Return 200 so Razorpay doesn't retry infinitely if it's our bug
        return "ERR", 200

# ==========================
# 8) BACKGROUND JOBS
# ==========================
def job_send_reminders():
    try:
        for user_id, subject, exp in fetch_due_reminders():
            try:
                left = max(0, (exp - datetime.now(timezone.utc)).days)
                bot.send_message(
                    user_id,
                    f"⏳ Reminder: Your <b>{subject}</b> access expires in {left} day(s).\n"
                    f"Pay again to extend for {DAYS_PER_SUB} days."
                )
                mark_reminded(user_id, subject)
            except Exception as e:
                print("Reminder send error:", e)
    except Exception as e:
        print("Reminder job error:", e)

def job_expire_and_kick():
    try:
        for user_id, subject, channel_id in fetch_expired():
            try:
                bot.ban_chat_member(channel_id, user_id)
                bot.unban_chat_member(channel_id, user_id)
            except Exception as e:
                print("Kick error:", e)
            finally:
                mark_expired(user_id, subject)
    except Exception as e:
        print("Expire job error:", e)

def start_scheduler():
    # every 30 minutes
    scheduler.add_job(job_send_reminders, "interval", minutes=30, id="reminders", replace_existing=True)
    scheduler.add_job(job_expire_and_kick, "interval", minutes=30, id="kicker", replace_existing=True)
    scheduler.start()

# ==========================
# 9) START EVERYTHING
# ==========================
if __name__ == "__main__":
    db_init()

    # Start Flask web server in a thread (Render expects a web server)
    def run_web():
        # IMPORTANT: after deploy, point Razorpay webhook to https://<your-render-url>/webhook
        app.run(host="0.0.0.0", port=8080, debug=False)

    threading.Thread(target=run_web, daemon=True).start()

    # Start background jobs
    start_scheduler()

    # Start Telegram polling
    print("✅ Bot is running. Do not close this tab.")
    bot.infinity_polling(skip_pending=True, timeout=60)
