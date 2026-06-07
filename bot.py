import os
import asyncio
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler,
    ContextTypes, filters
)

# =========================
# CONFIG
# =========================
ADMIN_ID = 7488034821

KPAY_NUMBER = "09401878226"
KPAY_NAME = "Li Li Naing"

WAVE_NUMBER = "09788599697"
WAVE_NAME = "Li Li Naing"

TIMEZONE = pytz.timezone("Asia/Yangon")

ADMIN_ROUTING = {}

# =========================
# STATES
# =========================
GET_ORDER, WAIT_ADMIN, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

# =========================
# 💎 YOUR FULL PRICE LIST
# =========================
PRICES = {
    "mmk_diamonds": {
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
    },

    "pass": {
        "weekly": 6500,
        "twilight": 35000
    },

    # extra adjustment system
    "mm_extra": 50,
    "sg_base": 2900
}


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 **Pepe GameShop မှ ကြိုဆိုပါတယ်**\n\n"
        "📩 သင့် Game ID ပို့ပါ\n"
        "ဥပမာ - Pepe 123456 (7788)\n\n"
        "⏳ Server စစ်ဆေးပြီး စျေးနှုန်းပို့ပေးပါမည်"
    )
    return GET_ORDER


# =========================
# ORDER
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text

    context.user_data["order"] = text
    context.user_data["user_id"] = user_id

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔍 SERVER CHECK REQUEST\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"User: {user_id}\n"
            f"Input: {text}\n\n"
            "👉 Reply to confirm server"
        )
    )

    ADMIN_ROUTING[msg.message_id] = {
        "user_id": user_id,
        "context": context
    }

    await update.message.reply_text("⏳ Server စစ်ဆေးနေပါသည်...")
    return WAIT_ADMIN


# =========================
# ADMIN HANDLER (NO PRICE TYPING)
# =========================
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply လုပ်ပါ")

    msg_id = update.message.reply_to_message.message_id

    if msg_id not in ADMIN_ROUTING:
        return await update.message.reply_text("Session expired")

    session = ADMIN_ROUTING[msg_id]
    user_id = session["user_id"]
    user_ctx = session["context"]

    mmk_text = "\n".join([
        f"💎{k} = {v:,} MMK"
        for k, v in PRICES["mmk_diamonds"].items()
    ])

    price_text = (
        "🎯 **Server Confirmed**\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💰 **Diamond Prices (MMK)**\n"
        f"{mmk_text}\n\n"
        "🎟 Pass Prices\n"
        f"Weekly Pass = {PRICES['pass']['weekly']:,} MMK\n"
        f"Twilight Pass = {PRICES['pass']['twilight']:,} MMK\n\n"
        "➕ Extra Info\n"
        f"MM Server +{PRICES['mm_extra']} MMK added\n"
        f"SG Server base = {PRICES['sg_base']} MMK equivalent\n\n"
        "💎 Amount ရိုက်ပေးပါ"
    )

    await context.bot.send_message(chat_id=user_id, text=price_text)

    del ADMIN_ROUTING[msg_id]

    user_ctx.user_data["flow"] = GET_AMOUNT


# =========================
# AMOUNT
# =========================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("flow") != GET_AMOUNT:
        return

    context.user_data["amount"] = update.message.text

    await update.message.reply_text(
        "🔍 **အတည်ပြုရန်**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📦 {context.user_data['order']}\n"
        f"💎 {context.user_data['amount']}\n\n"
        "YES ရိုက်ပါ"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":
        await update.message.reply_text(
            "💳 **Payment Info**\n\n"
            "KBZPay / Wave Money\n\n"
            f"{KPAY_NUMBER} ({KPAY_NAME})\n"
            f"{WAVE_NUMBER} ({WAVE_NAME})\n\n"
            "📸 Screenshot ပို့ပါ"
        )
        return WAIT_PAYMENT

    return ConversationHandler.END


# =========================
# PAYMENT
# =========================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    keyboard = [[
        InlineKeyboardButton("APPROVE", callback_data=f"acc|{user.id}"),
        InlineKeyboardButton("REJECT", callback_data=f"rej|{user.id}")
    ]]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=(
            "🆕 ORDER\n"
            f"User: {user.id}\n"
            f"Order: {context.user_data.get('order')}\n"
            f"Amount: {context.user_data.get('amount')}"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("Sent to admin")
    return ConversationHandler.END


# =========================
# CALLBACK
# =========================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    action, uid = q.data.split("|")
    uid = int(uid)

    if action == "acc":
        await context.bot.send_message(uid, "Approved. Sending diamonds...")
    else:
        await context.bot.send_message(uid, "Rejected")


# =========================
# MAIN
# =========================
async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order)],
            WAIT_ADMIN: [MessageHandler(filters.TEXT, lambda u, c: None)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.TEXT, handle_admin))
    app.add_handler(CallbackQueryHandler(callback))

    print("BOT RUNNING 🚀")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
