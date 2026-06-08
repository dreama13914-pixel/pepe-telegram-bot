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
# 💎 PRICE LIST (UNCHANGED)
# =========================
MMK_PRICES = {
    55: 4800,
    86: 5300,
    165: 14300,
    172: 15000,
    257: 22300,
    275: 23800,
    343: 30000,
    565: 48800,
    706: 61000,
    2195: 189000,
    3688: 317300,
    5532: 475900,
    9288: 799000
}

PASS_PRICES = {
    "weekly": 6500,
    "twilight": 35000
}

SG_EXTRA = 2900

SHOP_TZ = pytz.timezone("Asia/Yangon")


def shop_open():
    now = datetime.now(SHOP_TZ)
    minutes = now.hour * 60 + now.minute
    return 11 * 60 <= minutes <= 19 * 60 + 30


# =========================
# SAFE USER STORAGE
# =========================
USER_DATA = {}
ADMIN_MAP = {}


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not shop_open():
        await update.message.reply_text(
            "🔒 ဆိုင်ပိတ်ထားပါသည်\n\n"
            "🕚 11:00 AM - 7:30 PM"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 Pepe GameShop မှ ကြိုဆိုပါတယ်\n\n"
        "💎 Game ID ပို့ပါ"
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

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🔍 NEW ORDER\nID: {user_id}\n{text}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    ADMIN_MAP[msg.message_id] = user_id

    await update.message.reply_text("⏳ Admin စစ်ဆေးနေပါသည်...")

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
        await context.bot.send_message(uid, "❌ သင့် order ကို လက်မခံနိုင်ပါ")
        return

    USER_DATA[uid]["server"] = action

    await context.bot.send_message(
        uid,
        "🎯 Server Confirmed\n"
        f"🌍 Server: {action.upper()}\n\n"
        "💎 Amount ရိုက်ပါ (86 / weekly / twilight)"
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
        await update.message.reply_text("❌ Error, /start again")
        return ConversationHandler.END

    server = data.get("server", "mm")

    if value in MMK_PRICES:
        price = MMK_PRICES[value]
    elif value in PASS_PRICES:
        price = PASS_PRICES[value]
    else:
        await update.message.reply_text("❌ မရှိပါ")
        return

    if server == "sg":
        price += SG_EXTRA

    USER_DATA[user_id].update({
        "amount": value,
        "price": price
    })

    await update.message.reply_text(
        "🔍 ပြန်စစ်ပါ\n"
        f"📦 Item: {value}\n"
        f"🌍 Server: {server}\n"
        f"💰 Price: {price}\n\n"
        "YES ရိုက်ပါ"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":
        await update.message.reply_text(
            "💳 KBZPay / Wave Money\n"
            "Screenshot ပို့ပါ 📸"
        )
        return WAIT_PAYMENT


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
    main()main()
