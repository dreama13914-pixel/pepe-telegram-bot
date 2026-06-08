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

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

KBZPAY = "09401878226"
WAVEPAY = "09788599697"

SG_EXTRA = 2900
SHOP_TZ = pytz.timezone("Asia/Yangon")

# =========================
# 💎 PRICE LIST (YOUR STYLE KEPT)
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
# TIME CHECK
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
            "🔒 ဆိုင်ပိတ်ထားပါသည်\n"
            "🕚 11:00 AM - 7:30 PM"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Pepe Diamond Shop မှ ကြိုဆိုပါတယ်\n\n"
        "📌 Game ID ကို ဒီလိုပို့ပါ\n"
        "👉 Pepe 1600113465 (16740)\n\n"
        "💎 Diamond / Pass ရွေးချယ်ပါ"
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
        [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"mm_{user_id}")],
        [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"sg_{user_id}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        f"🔍 NEW ORDER\n{text}\n👤 USER: {user_id}",
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

    context.application.bot_data[f"user_{uid}"] = {
        "server": action
    }

    await context.bot.send_message(
        uid,
        f"🎯 Server Confirmed\n🌍 {action.upper()}\n\n"
        "💎 Amount ရိုက်ပါ\n"
        "👉 55 / 86 / weekly1 / weekly2 / weekly3 / twilight"
    )


# =========================
# AMOUNT
# =========================

async def amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    raw = update.message.text.lower().strip()

    data = context.application.bot_data.get(f"user_{user_id}")

    if not data:
        await update.message.reply_text("❌ /start ပြန်လုပ်ပါ")
        return ConversationHandler.END

    try:
        value = int(raw)
    except:
        value = raw

    price = None

    if isinstance(value, int) and value in BASE_PRICES:
        price = BASE_PRICES[value]
    elif isinstance(value, str) and value in PASS_PRICES:
        price = PASS_PRICES[value]

    if price is None:
        await update.message.reply_text("❌ မရှိပါ")
        return GET_AMOUNT

    if data["server"] == "sg":
        price += SG_EXTRA

    data["amount"] = value
    data["price"] = price

    await update.message.reply_text(
        f"🔍 CONFIRM ORDER\n\n"
        f"📦 Item: {value}\n"
        f"🌍 Server: {data['server'].upper()}\n"
        f"💰 Price: {price} MMK\n\n"
        "👉 YES လို့ရိုက်ပါ"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() != "yes":
        await update.message.reply_text("👉 YES လို့ပဲရိုက်ပါ")
        return CONFIRM

    await update.message.reply_text(
        "💳 PAYMENT INFO\n\n"
        f"KBZPay: {KBZPAY}\n"
        f"WavePay: {WAVEPAY}\n\n"
        "📸 ငွေလွှဲပြီး screenshot ပို့ပါ"
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

    await update.message.reply_text("✅ Order လက်ခံပြီးပါပြီ")
    return ConversationHandler.END


# =========================
# MAIN (FIXED FOR RENDER)
# =========================

def main():

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

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
