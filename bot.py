import os
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, CallbackQueryHandler, filters
)

ADMIN_ID = 7488034821

GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# =========================
# 💎 YOUR EXACT PRICE LIST (+50 MMK ADDED)
# =========================

MMK_PRICES = {
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

# =========================
# 🎟 WEEKLY PASS (FIXED PROPERLY)
# =========================
BASE_WEEKLY = 6500 + 50  # +50 rule

PASS_PRICES = {
    "weekly1": BASE_WEEKLY,
    "weekly2": BASE_WEEKLY * 2,
    "weekly3": BASE_WEEKLY * 3,
    "twilight": 35050
}

SG_EXTRA = 2900

SHOP_TZ = pytz.timezone("Asia/Yangon")


def shop_open():
    now = datetime.now(SHOP_TZ)
    minutes = now.hour * 60 + now.minute
    return 11 * 60 <= minutes <= 19 * 60 + 30


# =========================
# STORAGE
# =========================
USER_DATA = {}


# =========================
# START MESSAGE (KEEP SIMPLE)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not shop_open():
        await update.message.reply_text(
            "🔒 Shop closed\n🕚 11:00 AM - 7:30 PM"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Pepe Diamond Shop\n\n"
        "Send your Game ID like:\n"
        "Pepe 1600113465 (16740)"
    )

    return GET_ORDER


# =========================
# ORDER → ADMIN BUTTONS
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id
    text = update.message.text

    USER_DATA[user_id] = {"order": text}

    keyboard = [
        [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"mm_{user_id}")],
        [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"sg_{user_id}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        f"NEW ORDER\nID: {user_id}\n{text}",
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
        USER_DATA.pop(uid, None)
        return

    USER_DATA.setdefault(uid, {})
    USER_DATA[uid]["server"] = action

    await context.bot.send_message(
        uid,
        "🎯 Server Confirmed\n\n"
        f"🌍 Server: {action.upper()}\n\n"
        "Send amount:\n"
        "55 / 86 / 165 / weekly1 / weekly2 / weekly3 / twilight"
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

    data = USER_DATA.get(user_id)
    if not data:
        await update.message.reply_text("❌ /start again")
        return ConversationHandler.END

    server = data.get("server", "mm")

    if value in MMK_PRICES:
        price = MMK_PRICES[value]
    elif value in PASS_PRICES:
        price = PASS_PRICES[value]
    else:
        await update.message.reply_text("❌ Not found")
        return

    if server == "sg":
        price += SG_EXTRA

    USER_DATA[user_id].update({
        "amount": value,
        "price": price
    })

    await update.message.reply_text(
        "🔍 CONFIRM\n\n"
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
            "💳 KBZPay / Wave Money\n"
            "Send screenshot 📸"
        )
        return WAIT_PAYMENT


# =========================
# PAYMENT → ADMIN
# =========================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    await context.bot.forward_message(
        ADMIN_ID,
        user_id,
        update.message.message_id
    )

    await update.message.reply_text("✅ Done")
    return ConversationHandler.END


# =========================
# MAIN (RENDER SAFE)
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
