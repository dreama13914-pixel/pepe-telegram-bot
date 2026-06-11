import os
import json
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# ================= CONFIG =================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

STATE_GET_ID = "GET_ID"
STATE_CONFIRM_ID = "CONFIRM_ID"
STATE_WAIT_ADMIN_SERVER = "WAIT_ADMIN_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM_AMOUNT = "CONFIRM_AMOUNT"

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
    return {
        "MYANMAR": True,
        "SINGAPORE": True,
        "MALAYSIA": True,
        "PHILIPPINES": True,
        "INDONESIA": True
    }

server_status = load_server_status()

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

# ================= PRICE SHEETS =================

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

PRICE_SG_MY = """💎 SINGAPORE & MALAYSIA SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 7,450 MMK
💎86 = 7,950 MMK
💎165 = 16,950 MMK
💎172 = 17,650 MMK
💎257 = 24,950 MMK
💎275 = 26,450 MMK
💎343 = 32,650 MMK
💎565 = 51,450 MMK
💎706 = 63,650 MMK
💎2195 = 191,650 MMK
💎3688 = 319,950 MMK
💎5532 = 478,550 MMK
💎9288 = 801,650 MMK

🎟 Weekly Pass 1 = 9,150 MMK
🎟 Weekly Pass 2 = 15,700 MMK
🎟 Weekly Pass 3 = 22,250 MMK
🎟 Twilight Pass = 37,650 MMK
🎟 Starlight Card = 31,900 MMK
"""

PRICE_PH = """💎 PHILIPPINES SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 5,300 MMK
💎86 = 5,800 MMK
💎165 = 14,800 MMK
💎172 = 15,500 MMK
💎257 = 22,800 MMK
💎275 = 24,300 MMK
💎343 = 30,500 MMK
💎565 = 49,300 MMK
💎706 = 61,500 MMK
💎2195 = 189,500 MMK
💎3688 = 317,800 MMK
💎5532 = 476,400 MMK
💎9288 = 799,500 MMK

🎟 Weekly Pass 1 = 7,000 MMK
🎟 Weekly Pass 2 = 13,550 MMK
🎟 Weekly Pass 3 = 20,100 MMK
🎟 Twilight Pass = 35,500 MMK
🎟 Starlight Card = 29,750 MMK
"""

PRICE_ID = """💎 INDONESIA SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 5,320 MMK
💎86 = 5,820 MMK
💎165 = 14,820 MMK
💎172 = 15,520 MMK
💎257 = 22,820 MMK
💎275 = 24,320 MMK
💎343 = 30,520 MMK
💎565 = 49,320 MMK
💎706 = 61,520 MMK
💎2195 = 189,520 MMK
💎3688 = 317,820 MMK
💎5532 = 476,420 MMK
💎9288 = 799,520 MMK

🎟 Weekly Pass 1 = 7,020 MMK
🎟 Weekly Pass 2 = 13,570 MMK
🎟 Weekly Pass 3 = 20,120 MMK
🎟 Twilight Pass = 35,520 MMK
🎟 Starlight Card = 29,770 MMK
"""

# ================= START =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id

    if not is_shop_open():
        await update.message.reply_text("ဆိုင်ပိတ်ချိန်ပါ။ 11:00 - 7:30")
        return

    user_data[uid] = {"state": STATE_GET_ID}

    await update.message.reply_text(
        "🐸 Welcome!\nGame ID + Zone ID ရိုက်ထည့်ပါ"
    )

# ================= MESSAGE =================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()

    if uid not in user_data:
        user_data[uid] = {}

    state = user_data[uid].get("state")

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

    elif state == STATE_GET_AMOUNT:
        try:
            item = int(text)
        except:
            item = text.lower().replace(" ", "")

        server = user_data[uid].get("server", "MYANMAR")
        price = calc_price(server, item)

        if price is None:
            await update.message.reply_text("မှားနေတယ်")
            return

        user_data[uid]["temp_item"] = item
        user_data[uid]["temp_price"] = price
        user_data[uid]["state"] = STATE_CONFIRM_AMOUNT

        kb = [[
            InlineKeyboardButton("YES", callback_data=f"amtconf|yes|{uid}"),
            InlineKeyboardButton("NO", callback_data=f"amtconf|no|{uid}")
        ]]

        await update.message.reply_text(
            f"{item} = {price:,} MMK",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= CALLBACKS =================

async def id_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, choice, uid = q.data.split("|")
    uid = int(uid)

    if choice == "no":
        user_data[uid]["state"] = STATE_GET_ID
        await q.edit_message_text("ပြန်ရိုက်ပါ")
        return

    user_data[uid]["state"] = STATE_WAIT_ADMIN_SERVER

    kb = [
        [InlineKeyboardButton("MYANMAR", callback_data=f"admsrv|MYANMAR|{uid}")],
        [InlineKeyboardButton("SG", callback_data=f"admsrv|SINGAPORE|{uid}")],
        [InlineKeyboardButton("MY", callback_data=f"admsrv|MALAYSIA|{uid}")],
        [InlineKeyboardButton("PH", callback_data=f"admsrv|PHILIPPINES|{uid}")],
        [InlineKeyboardButton("ID", callback_data=f"admsrv|INDONESIA|{uid}")]
    ]

    await context.bot.send_message(uid, "Server choose:", reply_markup=InlineKeyboardMarkup(kb))
    await q.edit_message_text("Server selecting...")

async def amount_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, choice, uid = q.data.split("|")
    uid = int(uid)

    if choice == "no":
        user_data[uid]["state"] = STATE_GET_AMOUNT
        await q.edit_message_text("ပြန်ရိုက်ပါ")
        return

    user_data[uid]["item"] = user_data[uid]["temp_item"]
    user_data[uid]["price"] = user_data[uid]["temp_price"]

    await q.edit_message_text(
        f"Confirmed: {user_data[uid]['item']} = {user_data[uid]['price']:,} MMK"
    )

async def admin_server(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    _, server, uid = q.data.split("|")
    uid = int(uid)

    user_data[uid]["server"] = server
    user_data[uid]["state"] = STATE_GET_AMOUNT

    sheet = (
        PRICE_MYANMAR if server == "MYANMAR"
        else PRICE_SG_MY if server in ["SINGAPORE", "MALAYSIA"]
        else PRICE_PH if server == "PHILIPPINES"
        else PRICE_ID
    )

    await context.bot.send_message(uid, sheet)
    await q.edit_message_text("Done")

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.add_handler(CallbackQueryHandler(id_confirm, pattern="^idconf\\|"))
    app.add_handler(CallbackQueryHandler(amount_confirm, pattern="^amtconf\\|"))
    app.add_handler(CallbackQueryHandler(admin_server, pattern="^admsrv\\|"))

    print("RUNNING BOT")
    app.run_polling()

if __name__ == "__main__":
    main()
