import os
import json
from datetime import datetime
import pytz
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# ================= CONFIG =================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

STATE_GET_ID = "GET_ID"
STATE_CONFIRM_ID = "CONFIRM_ID"
STATE_WAIT_ADMIN_SERVER = "WAIT_ADMIN_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM_AMOUNT = "CONFIRM_AMOUNT"
STATE_CONFIRM = "CONFIRM"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

user_data = {}
STATUS_FILE = "server_status.txt"

# ================= SHOP TIME =================

def is_shop_open():
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).time()
    start = datetime.strptime("11:00", "%H:%M").time()
    end = datetime.strptime("19:30", "%H:%M").time()
    return start <= now <= end

# ================= SERVER STATUS =================

def load_server_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {"MYANMAR": True, "SINGAPORE": True, "MALAYSIA": True, "PHILIPPINES": True, "INDONESIA": True}

def save_server_status(data):
    with open(STATUS_FILE, "w") as f:
        json.dump(data, f)

server_status = load_server_status()

SERVER_FLAGS = {
    "MYANMAR": "🇲🇲",
    "SINGAPORE": "🇸🇬",
    "MALAYSIA": "🇲🇾",
    "PHILIPPINES": "🇵🇭",
    "INDONESIA": "🇮🇩"
}

# ================= PRICING SYSTEM =================

BASE_ADJUST = {
    "MYANMAR": 0,
    "SINGAPORE": 2600,
    "MALAYSIA": 2600,
    "PHILIPPINES": 450,
    "INDONESIA": 470
}

MYANMAR_BASE = {
    55: 4850, 86: 5350, 165: 14350, 172: 15050, 257: 22350,
    275: 23850, 343: 30050, 565: 48850, 706: 61050,
    2195: 189050, 3688: 317350, 5532: 475950, 9288: 799050
}

MYANMAR_PASS = {
    "wp1": 6550,
    "wp2": 13100,
    "wp3": 19650,
    "twi": 35050,
    "starlight": 29300
}

def calc_price(server, item):
    adj = BASE_ADJUST.get(server, 0)

    if isinstance(item, int):
        base = MYANMAR_BASE.get(item)
    else:
        item = item.replace(" ", "").lower()
        base = MYANMAR_PASS.get(item)

    if base is None:
        return None

    return base + adj

# ================= MYANMAR PRICE TEXT (UNCHANGED STYLE) =================

PRICE_MYANMAR = """💎 MYANMAR SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 4,850 MMK
💎86 = 5,350 MMK
💎165 = 14,350 MMK
💎172 = 15,050 MMK
💎257 = 22,350 MMK
💎275 = 23,850 MMK
💎343 = 30,050 MMK
💎565 = 48,850 MMK
💎706 = 61,050 MMK
💎2195 = 189,050 MMK
💎3688 = 317,350 MMK
💎5532 = 475,950 MMK
💎9288 = 799,050 MMK

🎟 Weekly Pass 1 = 6,550 MMK
🎟 Weekly Pass 2 = 13,100 MMK
🎟 Weekly Pass 3 = 19,650 MMK
🎟 Twilight Pass = 35,050 MMK
🎟 Starlight Card = 29,300 MMK
"""

# ================= AUTO GENERATE OTHER SERVERS =================

def build_price(server):
    adj = BASE_ADJUST[server]
    flag = SERVER_FLAGS[server]

    text = f"{flag} {server} SERVER ဈေးနှုန်းများ\n\n❗️Minimum order = 55 💎\n\n"

    for k, v in MYANMAR_BASE.items():
        text += f"💎{k} = {v + adj} MMK\n"

    text += f"""
🎟 Weekly Pass 1 = {MYANMAR_PASS['wp1'] + adj} MMK
🎟 Weekly Pass 2 = {MYANMAR_PASS['wp2'] + adj} MMK
🎟 Weekly Pass 3 = {MYANMAR_PASS['wp3'] + adj} MMK
🎟 Twilight Pass = {MYANMAR_PASS['twi'] + adj} MMK
🎟 Starlight Card = {MYANMAR_PASS['starlight'] + adj} MMK
"""

    return text

PRICE_SG = build_price("SINGAPORE")
PRICE_PH = build_price("PHILIPPINES")
PRICE_ID = build_price("INDONESIA")

# ================= START HANDLER =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id

    if not is_shop_open():
        await update.message.reply_text("ဆိုင်ပိတ်ချိန်ပါ။ 11:00 - 7:30 အတွင်းလာပါ။")
        return

    user_data[uid] = {"state": STATE_GET_ID}

    await update.message.reply_text(
        "🐸 Welcome!\n\nGame ID + Zone ID ရိုက်ထည့်ပါ\nExample: 123456789 (1234)"
    )

# ================= MESSAGE HANDLER =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()

    if not is_shop_open():
        await update.message.reply_text("ဆိုင်ပိတ်ချိန်ပါ။")
        return

    state = user_data.get(uid, {}).get("state")

    if state == STATE_GET_ID:
        user_data[uid]["id"] = text
        user_data[uid]["state"] = STATE_CONFIRM_ID

        kb = [[
            InlineKeyboardButton("YES", callback_data=f"idconf|yes|{uid}"),
            InlineKeyboardButton("NO", callback_data=f"idconf|no|{uid}")
        ]]

        await update.message.reply_text(
            f"ID: {text} မှန်လား?",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return

    if state == STATE_GET_AMOUNT:
        try:
            item = int(text)
        except:
            item = text.lower().replace(" ", "")

        server = user_data[uid]["server"]
        price = calc_price(server, item)

        if price is None:
            await update.message.reply_text("မှားနေတယ် ပြန်ရိုက်ပါ")
            return

        user_data[uid]["temp_item"] = item
        user_data[uid]["temp_price"] = price
        user_data[uid]["state"] = STATE_CONFIRM_AMOUNT

        kb = [[
            InlineKeyboardButton("YES", callback_data=f"amtconf|yes|{uid}"),
            InlineKeyboardButton("NO", callback_data=f"amtconf|no|{uid}")
        ]]

        await update.message.reply_text(
            f"Item + Price မှန်လား?\n{item} = {price}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= SERVER SELECTION =================

async def admin_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, server, uid = query.data.split("|")
    uid = int(uid)

    user_data[uid]["server"] = server
    user_data[uid]["state"] = STATE_GET_AMOUNT

    sheet = PRICE_MYANMAR if server == "MYANMAR" else (
        PRICE_SG if server in ["SINGAPORE", "MALAYSIA"]
        else PRICE_PH if server == "PHILIPPINES"
        else PRICE_ID
    )

    await context.bot.send_message(uid, sheet)
    await query.edit_message_text("Server set done")

# ================= BOT START =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(admin_server, pattern="^admsrv\\|"))

    print("RUNNING BOT")
    app.run_polling()

if __name__ == "__main__":
    main()
