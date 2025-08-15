import os
import sqlite3
from datetime import datetime, timedelta, timezone

from flask import Flask, request
import telebot
import razorpay
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler

# ==========================
# 1) READ SECRETS FROM ENV
# ==========================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

# Public base URL of your Render web service
PUBLIC_BASE_URL = "https://pyqp.onrender.com"  # <- keep this as your Render URL

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
        "4 in 1": -1002213153230,  # renamed from "All in One"
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
    },
}

# Default price for most subjects
PRICE_INR_DEFAULT = 49
# Special price for Pilot -> "4 in 1"
PRICE_INR_4IN1 = 149

DAYS_PER_SUB = 30
REMINDER_DAYS_BEFORE = 2

# ==========================
# 3) INIT TELEGRAM & RAZORPAY
# ==========================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
rz_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

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
            status TEXT NOT NULL,
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
# 5) MENUS & HELPERS
# ==========================
def get_price(stream: str, subject: str) -> int:
    # Only Pilot -> "4 in 1" is ₹149; everything else uses default price
    if stream == "pilot" and subject == "4 in 1":
        return PRICE_INR_4IN1
    return PRICE_INR_DEFAULT

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

# --- FAQ data (stable IDs so callback_data stays short/clean) ---
CONTACT_TEXT = (
    "🌐 Website: <a href=\"https://examairways.com\">examairways.com</a>\n"
    "📧 Email: <a href=\"mailto:examairways@gmail.com\">examairways@gmail.com</a>\n"
    "📸 Instagram: <a href=\"https://www.instagram.com/examairways?igsh=Yjl1YzBmNHAwMGdp\">@examairways</a>"
)

FAQ_ITEMS = [
    {
        "id": "pay",
        "q": "How to make payment?",
        "a": "Open the bot, choose your stream and subject, tap Pay (Razorpay). After successful payment you'll be added automatically (join request approved) or receive a single-use invite link."
    },
    {
        "id": "validity",
        "q": "What is the validity?",
        "a": "Each subscription is valid for 30 days. Special pricing: Pilot '4 in 1' is ₹149/month; other subjects are ₹49/month."
    },
    {
        "id": "renew",
        "q": "How to renew?",
        "a": "Before expiry (or after), just pay again for the same subject. Your expiry will extend by 30 days from the current expiry if still active, or from today if expired."
    },
    {
        "id": "access",
        "q": "How do I get access after payment?",
        "a": "If you already tapped Join on the private group/channel, the bot approves your request automatically after payment. If not, you'll receive a single-use invite link valid until your expiry."
    },
    {
        "id": "refund",
        "q": "Refund Policy",
        "a": "Digital content cannot be refunded once accessed."
    },
    {
        "id": "contact",
        "q": "Contact",
        "a": CONTACT_TEXT
    },
]

FAQ_BY_ID = {i["id"]: i for i in FAQ_ITEMS}

def faq_menu():
    kb = InlineKeyboardMarkup()
    for item in FAQ_ITEMS:
        kb.add(InlineKeyboardButton(item["q"], callback_data=f"faq_q:{item['id']}"))
    kb.add(InlineKeyboardButton("⬅️ Back", callback_data="back"))
    return kb

# ==========================
# 6) BOT HANDLERS (INLINE UI)
# ==========================
@bot.message_handler(commands=["start"])
def cmd_start(message):
    welcome = (
        "Select your category below.\n\n"
        f"{CONTACT_TEXT}"
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu(), disable_web_page_preview=True)

@bot.callback_query_handler(func=lambda c: c.data == "faq")
def cb_faq(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"Select a question.\n\n{CONTACT_TEXT}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=faq_menu(),
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("faq_q:"))
def cb_faq_question(call):
    bot.answer_callback_query(call.id)
    fid = call.data.split("faq_q:", 1)[1]
    item = FAQ_BY_ID.get(fid)
    if not item:
        bot.answer_callback_query(call.id, "Not found.")
        return
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⬅️ Back to FAQ", callback_data="faq"))
    bot.edit_message_text(
        f"<b>{item['q']}</b>\n\n{item['a']}\n\n{CONTACT_TEXT}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=kb,
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda c: c.data == "back")
def cb_back(call):
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"Select your category.\n\n{CONTACT_TEXT}",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=main_menu(),
        disable_web_page_preview=True
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("stream:"))
def cb_stream(call):
    bot.answer_callback_query(call.id)
    stream = call.data.split(":", 1)[1]
    bot.edit_message_text(
        f"Select subject for <b>{stream.upper()}</b>:",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=subjects_menu(stream)
    )

@bot.callback_query_handler(func=lambda c: c.data.startswith("subject:"))
def cb_subject(call):
    bot.answer_callback_query(call.id)
    _, stream, subject = call.data.split(":", 2)
    try:
        price = get_price(stream, subject)
        payment = rz_client.payment_link.create({
            "amount": price * 100,
            "currency": "INR",
            "description": f"Subscription for {subject}",
            "notes": {
                "user_id": call.from_user.id,
                "username": call.from_user.username or "",
                "stream": stream,
                "subject": subject,
            },
            "notify": {"sms": False, "email": False},
            "callback_url": PUBLIC_BASE_URL,   # Razorpay will redirect here (optional)
            "callback_method": "get",
        })

        bot.edit_message_text(
            f"Pay ₹{price}/month for <b>{subject}</b>.\n\n"
            f"After successful payment:\n"
            f"• If you've already tapped <i>Join</i> on the group, you'll be auto-approved.\n"
            f"• Otherwise, you'll receive a single-use invite link.\n\n"
            f"{CONTACT_TEXT}",
            call.message.chat.id,
            call.message.message_id,
            disable_web_page_preview=True
        )
        bot.send_message(call.message.chat.id, payment.get("short_url"))
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ Error creating payment link: {e}")

# ==========================
# 7) FLASK WEB SERVER (RAZORPAY + TELEGRAM WEBHOOKS)
# ==========================
app = Flask(__name__)

@app.get("/")
def home():
    return "OK", 200

# Razorpay webhook
@app.post("/webhook")
def webhook():
    try:
        payload = request.data.decode("utf-8")
        data = request.get_json(force=True)
        signature = request.headers.get("X-Razorpay-Signature", "")

        # Verify webhook signature if configured
        if RAZORPAY_WEBHOOK_SECRET:
            try:
                razorpay.Utility.verify_webhook_signature(payload, signature, RAZORPAY_WEBHOOK_SECRET)
            except Exception:
                return "Invalid signature", 400

        # Handle payment_link.paid
        if data.get("event") == "payment_link.paid":
            pl = data["payload"]["payment_link"]["entity"]
            notes = pl.get("notes", {})
            user_id = int(notes.get("user_id"))
            username = notes.get("username") or ""
            stream = notes.get("stream")
            subject = notes.get("subject")
            channel_id = CHANNELS.get(stream, {}).get(subject)

            if not channel_id:
                bot.send_message(
                    user_id,
                    "⚠️ Payment received, but the channel was not found.\n\n"
                    f"{CONTACT_TEXT}",
                    disable_web_page_preview=True
                )
                return "OK", 200

            new_expiry = upsert_subscription(user_id, username, stream, subject, channel_id)

            # 1) Try to approve a pending join request
            link = None
            try:
                bot.approve_chat_join_request(channel_id, user_id)
            except Exception:
                # 2) Fallback to a single-use invite link valid until expiry
                try:
                    invite = bot.create_chat_invite_link(
                        channel_id,
                        expire_date=int(new_expiry.timestamp()),
                        member_limit=1
                    )
                    link = invite.invite_link
                except Exception:
                    link = None

            # Notify the user
            msg = (
                "✅ <b>Payment received!</b>\n\n"
                f"Access: <b>{subject}</b>\n"
                f"Valid till: <code>{new_expiry}</code>\n"
            )
            if link:
                msg += f"Join link: {link}\n\n"
            else:
                msg += "You have been auto-approved (if you had a pending join request).\n\n"

            msg += CONTACT_TEXT
            bot.send_message(user_id, msg, disable_web_page_preview=True)

        return "OK", 200
    except Exception:
        return "ERR", 200

# Telegram webhook endpoint (must be unique path)
@app.post(f"/telegram/{BOT_TOKEN}")
def telegram_webhook():
    try:
        update = telebot.types.Update.de_json(request.get_data().decode("utf-8"))
        bot.process_new_updates([update])
    except Exception:
        # Avoid leaking errors to Telegram
        pass
    return "OK", 200

# ==========================
# 8) BACKGROUND JOBS
# ==========================
scheduler = BackgroundScheduler()

def job_send_reminders():
    for user_id, subject, exp in fetch_due_reminders():
        left = max(0, (exp - datetime.now(timezone.utc)).days)
        bot.send_message(
            user_id,
            f"⏳ Reminder: Your <b>{subject}</b> subscription expires in {left} day(s).\n"
            f"Renew any time to extend access by 30 days.\n\n"
            f"{CONTACT_TEXT}",
            disable_web_page_preview=True
        )
        mark_reminded(user_id, subject)

def job_expire_and_kick():
    for user_id, subject, channel_id in fetch_expired():
        try:
            # Works for groups/supergroups; for channels, bot needs admin rights
            bot.ban_chat_member(channel_id, user_id)
            bot.unban_chat_member(channel_id, user_id)
        except Exception:
            pass
        mark_expired(user_id, subject)

def start_scheduler():
    # Run every 30 minutes
    scheduler.add_job(job_send_reminders, "interval", minutes=30, id="reminders", replace_existing=True)
    scheduler.add_job(job_expire_and_kick, "interval", minutes=30, id="kicker", replace_existing=True)
    scheduler.start()

# ==========================
# 9) START (WEBHOOK MODE)
# ==========================
if __name__ == "__main__":
    db_init()
    start_scheduler()

    # Set Telegram webhook to your Render URL
    # (re-set on each boot to be safe)
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{PUBLIC_BASE_URL}/telegram/{BOT_TOKEN}")
    except Exception:
        # If this fails, Telegram will keep previous webhook – usually fine
        pass

    # Start Flask (no polling)
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
