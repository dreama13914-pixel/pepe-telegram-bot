import os
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

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # FIXED (must be int)

GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

SG_EXTRA = 2900

SHOP_TZ = pytz.timezone("Asia/Yangon")

# =========================
# PRICE LIST
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
# SHOP TIME CHECK
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
        await update.message.reply_text(
            "🔒 ဆိုင်ပိတ်ထားပါသည်\n🕚 11:00 AM - 7:30 PM"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Pepe Diamond Shop မှ ကြိုဆိုပါတယ်\n\n"
        "📌 Game ID ပို့ပါ\n"
        "👉 Example: Pepe 1600113465 (16740)"
    )

    return GET_ORDER


# =========================
# USER ORDER
# =========================

async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    text = update.message.text

    context.user_data["order"] = text

    keyboard = [
        [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"mm_{user_id}")],
        [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"sg_{user_id}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔍 NEW ORDER\n{text}\nUSER: {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Admin checking...")
    return GET_AMOUNT


# =========================
# ADMIN BUTTONS
# =========================

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "ban":
        await context.bot.send_message(uid, "❌ Order rejected")
        return

    context.user_data[uid] = {"server": action}

    await context.bot.send_message(
        uid,
        f"🎯 Server Confirmed: {action.upper()}\n"
        "💎 Amount ရိုက်ပါ (55 / 86 / weekly1 / weekly2 / weekly3 / twilight)"
    )


# =========================
# AMOUNT
# =========================

async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    raw = update.message.text.lower().strip()

    try:
        value = int(raw)
    except:
        value = raw

    data = context.user_data.get(user_id)
    if not data:
        await update.message.reply_text("❌ /start again")
        return ConversationHandler.END

    server = data.get("server", "mm")

    if value in BASE_PRICES:
        price = BASE_PRICES[value]
    elif value in PASS_PRICES:
        price = PASS_PRICES[value]
    else:
        await update.message.reply_text("❌ Not found")
        return GET_AMOUNT

    if server == "sg":
        price += SG_EXTRA

    context.user_data[user_id].update({
        "amount": value,
        "price": price
    })

    await update.message.reply_text(
        f"🔍 CONFIRM\n"
        f"Item: {value}\n"
        f"Server: {server}\n"
        f"Price: {price} MMK\n\n"
        "Type YES"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":

        await update.message.reply_text(
            f"💳 PAYMENT INFO\n\n"
            f"KBZPay: {KBZPAY}\n"
            f"WavePay: {WAVEPAY}\n\n"
            "📸 Screenshot ပို့ပါ"
        )

        return WAIT_PAYMENT

    await update.message.reply_text("Type YES to confirm")
    return CONFIRM


# =========================
# PAYMENT
# =========================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user_id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Order received")
    return ConversationHandler.END


# =========================
# MAIN
# =========================

def main():

    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

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

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
