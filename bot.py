import os
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, CallbackQueryHandler, filters
)

ADMIN_ID = "YOUR_ID"

GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# =========================
# 💳 PAYMENT INFO
# =========================
KBZPAY = "09401878226"
WAVEPAY = "09788599697"

# =========================
# 💎 PRICE LIST (+50 MMK ADDED)
# =========================
BASE_PRICES = {
💎 Diamond ဈေးများ

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

🎟 Pass ဈေးများ

🎟 Weekly Pass 1 = 6,550 MMK
🎟 Weekly Pass 2 = 13,100 MMK
🎟 Weekly Pass 3 = 19,650 MMK
🎟 Twilight Pass = 35,050 MMK
}

PASS_PRICES = {
🎟 Pass ဈေးများ

🎟 Weekly Pass 1 = 6,550 MMK
🎟 Weekly Pass 2 = 13,100 MMK
🎟 Weekly Pass 3 = 19,650 MMK
🎟 Twilight Pass = 35,050 MMK
}

SG_EXTRA = 2900

# =========================
# TIME CHECK
# =========================
SHOP_TZ = pytz.timezone("Asia/Yangon")

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
# ORDER → ADMIN BUTTONS
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
        text=f"🔍 NEW ORDER\n👤 ID: {text}\n🆔 USER: {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Admin checking...")
    return GET_AMOUNT


# =========================
# ADMIN BUTTON HANDLER
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
        "🎯 Server Confirmed\n"
        f"🌍 Server: {action.upper()}\n\n"
        "💎 Amount ရိုက်ပါ (55 / 86 / weekly1 / weekly2 / weekly3 / twilight)"
    )


# =========================
# AMOUNT HANDLER
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
        return

    if server == "sg":
        price += SG_EXTRA

    context.user_data[user_id].update({
        "amount": value,
        "price": price
    })

    await update.message.reply_text(
        "🔍 CONFIRM ORDER\n"
        f"📦 Item: {value}\n"
        f"🌍 Server: {server}\n"
        f"💰 Price: {price} MMK\n\n"
        "Type YES to continue"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":

        await update.message.reply_text(
            "💳 PAYMENT INFO\n\n"
            f"KBZPay: {KBZPAY}\n"
            f"WavePay: {WAVEPAY}\n\n"
            "ငွေလွှဲပြီး screenshot ပို့ပါ 📸"
        )

        return WAIT_PAYMENT


# =========================
# PAYMENT → ADMIN
# =========================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    await context.bot.forward_message(
        chat_id=ADMIN_ID,
        from_chat_id=user_id,
        message_id=update.message.message_id
    )

    await update.message.reply_text("✅ Order received. Thank you!")

    return ConversationHandler.END


# =========================
# MAIN (RENDER FIXED)
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
