import os
import asyncio
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, CallbackQueryHandler, filters
)

# =========================
# CONFIG
# =========================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

SG_EXTRA = 2900
SHOP_TZ = pytz.timezone("Asia/Yangon")

# =========================
# PRICES
# =========================

BASE_PRICES = {
    55: 4850,
    86: 5350,
    165: 14350,
    172: 15050,
    257: 22350,
    275: 23850,
    343: 30050,
    565: 48850,
    706: 61050,
    2195: 189050,
    3688: 317350,
    5532: 475950,
    9288: 799050
}

PASS_PRICES = {
    "weekly1": 6550,
    "weekly2": 13100,
    "weekly3": 19650,
    "twilight": 35050
}

# =========================
# SHOP TIME
# =========================

def shop_open():
    now = datetime.now(SHOP_TZ)
    minutes = now.hour * 60 + now.minute
    return 11 * 60 <= minutes <= 19 * 60 + 30


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not shop_open():
        await update.message.reply_text("🔒 Shop closed\n11:00 - 19:30")
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Welcome\nSend your Game ID"
    )

    return GET_ORDER


# =========================
# ORDER
# =========================

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    text = update.message.text

    context.user_data["order"] = text

    keyboard = [
        [InlineKeyboardButton("MM", callback_data=f"mm_{user_id}")],
        [InlineKeyboardButton("SG", callback_data=f"sg_{user_id}")],
        [InlineKeyboardButton("BAN", callback_data=f"ban_{user_id}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        f"NEW ORDER\n{text}\nUSER: {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("Waiting admin...")
    return GET_AMOUNT


# =========================
# CALLBACK (ADMIN)
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "ban":
        await context.bot.send_message(uid, "❌ Rejected")
        return

    context.application.bot_data[f"user_{uid}"] = {
        "server": action
    }

    await context.bot.send_message(
        uid,
        f"Server: {action.upper()}\nSend amount (55, 86, weekly1...)"
    )


# =========================
# AMOUNT
# =========================

async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    raw = update.message.text.lower().strip()

    data = context.application.bot_data.get(f"user_{user_id}")

    if not data:
        await update.message.reply_text("❌ /start again")
        return ConversationHandler.END

    try:
        value = int(raw)
    except:
        value = raw

    if isinstance(value, int) and value in BASE_PRICES:
        price = BASE_PRICES[value]
    elif isinstance(value, str) and value in PASS_PRICES:
        price = PASS_PRICES[value]
    else:
        await update.message.reply_text("❌ Not found")
        return GET_AMOUNT

    if data["server"] == "sg":
        price += SG_EXTRA

    data["amount"] = value
    data["price"] = price

    await update.message.reply_text(
        f"CONFIRM\nItem: {value}\nPrice: {price}\nType YES"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() != "yes":
        await update.message.reply_text("Type YES")
        return CONFIRM

    await update.message.reply_text(
        f"Pay:\nKBZ: {KBZPAY}\nWave: {WAVEPAY}\nSend screenshot"
    )

    return WAIT_PAYMENT


# =========================
# PAYMENT
# =========================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    await context.bot.forward_message(
        ADMIN_ID,
        user_id,
        update.message.message_id
    )

    await update.message.reply_text("✅ Received")
    return ConversationHandler.END


# =========================
# RUNNER (FIX FOR RENDER + PYTHON 3.14 ISSUE)
# =========================

async def run():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(buttons))

    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.idle()


if __name__ == "__main__":
    asyncio.run(run())
