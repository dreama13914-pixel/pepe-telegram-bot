import os
import json
import re
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
STATE_WAIT_IGN_CHECK = "WAIT_IGN_CHECK"
STATE_WAIT_ADMIN_SERVER = "WAIT_ADMIN_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM_AMOUNT = "CONFIRM_AMOUNT"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

user_data = {}

# ================= HELPERS =================

def get_user_identity(user):
    if user.username:
        return f"@{user.username}"
    name = (user.first_name or "")
    last = (user.last_name or "")
    return (name + " " + last).strip() or "NoNameUser"

# ================= SHOP TIME =================

def is_shop_open():
    tz = pytz.timezone('Asia/Yangon')
    now = datetime.now(tz).time()
    start = datetime.strptime("11:00", "%H:%M").time()
    end = datetime.strptime("19:30", "%H:%M").time()
    return start <= now <= end

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
    "starlight": 25700,
    "starlightcard": 25700,
    "star": 25700
}

def calc_price(server, item):
    adj = BASE_ADJUST.get(server, 0)

    if isinstance(item, int):
        base = MYANMAR_BASE.get(item)
    else:
        item = str(item).replace(" ", "").lower()
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
🎟 Starlight Card = 25,700 MMK"""

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
🎟 Starlight Card = 28,300 MMK"""

PRICE_PH = """💎 PHILIPPINES SERVER ဈေးနှုန်းများ

❗️Minimum order = 55 💎

💎55 = 5,300 MMK
💎86 = 5,800 MMK
💎165 = 14,800 MMK
💎172 = 15,500 MMK
💎227 = 22,800 MMK
💎275 = 24,300 MMK
💎343 = 30,500 MMK
💎565 = 49,300 MMK
💎706 = 61,500 MMK
💎2195 = 189,500 MMK
💎3688 = 317,800 MMK
💎5532 = 476,400 MMK
💎9288 = 799,500 MMK"""

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
💎9288 = 799,520 MMK"""

# ================= HANDLERS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id

    if not is_shop_open():
        await update.message.reply_text("⛔ ဆိုင်ပိတ်နေပါပြီ ဆိုင်ဖွင့်ချိန်မှာ မနက် ၁၁ နာရီမှ ည ၇ ခွဲဖြစ်ပါသည်")
        return

    user_data[uid] = {"state": STATE_GET_ID}
    await update.message.reply_text("🐸 မင်္ဂလာပါ Pepe's MLBB Diamond Shop မှကြိုဆိုပါသည် ✨\nGame ID နဲ့ Zone ID ကို ရိုက်ထည့်ပေးပါ။\nဥပမာ - 123456789 (1234)")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    text = update.message.text.strip()
    user = update.effective_user

    if uid not in user_data:
        user_data[uid] = {}

    state = user_data[uid].get("state")

    if state == STATE_GET_ID:
        user_data[uid]["id"] = text
        user_data[uid]["username"] = get_user_identity(user)
        user_data[uid]["state"] = STATE_CONFIRM_ID

        kb = [[
            InlineKeyboardButton("✔ YES", callback_data=f"idconf|yes|{uid}"),
            InlineKeyboardButton("❌ NO", callback_data=f"idconf|no|{uid}")
        ]]

        await update.message.reply_text(
            f"ရိုက်ထည့်လိုက်သော ID: {text}\nမှန်ပါသလား?",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif state == STATE_GET_AMOUNT:
        quantity = 1
        clean_text = text.lower().replace(" ", "")

        try:
            item = int(clean_text)
        except ValueError:
            match = re.match(r"([a-z]+)(\d+)$", clean_text)
            if match:
                item = match.group(1)
                quantity = int(match.group(2))
            else:
                item = clean_text

        server = user_data[uid].get("server", "MYANMAR")
        single_price = calc_price(server, item)

        if single_price is None:
            await update.message.reply_text("❌ မှားယွင်းနေပါသည်။ ပြန်လည်ရိုက်ထည့်ပါ။")
            return

        price = single_price * quantity
        display_item = f"{item.upper()} x{quantity}" if quantity > 1 else item.upper()

        user_data[uid]["temp_item"] = display_item
        user_data[uid]["temp_price"] = price
        user_data[uid]["state"] = STATE_CONFIRM_AMOUNT

        kb = [[
            InlineKeyboardButton("✔ YES", callback_data=f"amtconf|yes|{uid}"),
            InlineKeyboardButton("❌ NO", callback_data=f"amtconf|no|{uid}")
        ]]

        await update.message.reply_text(
            f"{display_item} = {price:,} MMK မှန်ပါသလား?",
            reply_markup=InlineKeyboardMarkup(kb)
        )

# ================= PHOTO (FIXED → FORWARD SYSTEM) =================

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_chat.id
    user = update.effective_user

    if uid not in user_data or user_data[uid].get("state") != STATE_WAIT_PAYMENT:
        return

    game_id = user_data[uid].get("id")
    item = user_data[uid].get("item")
    price = user_data[uid].get("price")
    server = user_data[uid].get("server")

    identity = get_user_identity(user)

    caption = f"""📩 ငွေလွှဲဖြတ်ပိုင်း ရောက်ရှိလာပါသည် 💰

👤 User: {identity}
🆔 Telegram ID: `{uid}`
🎮 Game ID: {game_id}
🌍 Server: {server}
🛒 Item: {item}
💵 Price: {price:,} MMK"""

    kb = [
        [InlineKeyboardButton("✅ Accept", callback_data=f"pay|accept|{uid}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"pay|reject|{uid}")]
    ]

    # 🔥 REAL TRANSCRIPT FORWARD
    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    )

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=caption,
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode="Markdown"
    )

    await update.message.reply_text("✔ ဖြတ်ပိုင်းကို ပို့ပြီးပါပြီ။ Admin စစ်ဆေးနေပါသည်...")

# ================= CALLBACKS (UNCHANGED CORE) =================

async def id_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    _, choice, uid = q.data.split("|")
    uid = int(uid)

    if choice == "no":
        user_data[uid]["state"] = STATE_GET_ID
        await q.edit_message_text("ပြန်လည်စတင်ရန် /start ကိုနှိပ်ပါ")
        return

    user_data[uid]["state"] = STATE_WAIT_IGN_CHECK

    kb = [
        [InlineKeyboardButton("✔ IGN OK", callback_data=f"ign|yes|{uid}")],
        [InlineKeyboardButton("❌ IGN NOT FOUND", callback_data=f"ign|no|{uid}")]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📥 IGN CHECK\nGame ID: `{user_data[uid]['id']}`",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    await q.edit_message_text("🔍 Admin စစ်ဆေးနေပါသည်...")

# (rest of your callbacks stay same — unchanged logic)

# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.add_handler(CallbackQueryHandler(id_confirm, pattern="^idconf\\|"))

    PORT = int(os.getenv("PORT", "8000"))
    RENDER_URL = os.getenv("RENDER_EXTERNAL_URL")

    if RENDER_URL:
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{RENDER_URL}/{BOT_TOKEN}"
        )
    else:
        app.run_polling()

if __name__ == "__main__":
    main()
