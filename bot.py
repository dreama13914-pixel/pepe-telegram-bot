import os
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

ADMIN_ROUTING = {}

# =========================
# STATES
# =========================
GET_ORDER, WAIT_ADMIN, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

# =========================
# PRICE LIST (YOUR DATA)
# =========================
PRICES = {
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

PASS = {
    "weekly": 6500,
    "twilight": 35000
}

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 **Pepe GameShop မှ ကြိုဆိုပါတယ်**\n\n"
        "📩 Game ID ပို့ပါ\n"
        "ဥပမာ - Pepe 123456 (7788)\n\n"
        "⏳ Server စစ်ဆေးပြီး စျေးနှုန်းပို့မည်"
    )
    return GET_ORDER


# =========================
# ORDER
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text

    context.user_data["order"] = text

    msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔍 SERVER CHECK\n"
            "━━━━━━━━━━━━━━━\n"
            f"User: {user_id}\n"
            f"Input: {text}\n\n"
            "Reply to confirm server"
        )
    )

    ADMIN_ROUTING[msg.message_id] = {
        "user_id": user_id,
        "context": context
    }

    await update.message.reply_text("⏳ Checking server...")
    return WAIT_ADMIN


# =========================
# ADMIN CONFIRM (NO LOOP CRASH)
# =========================
async def handle_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply to request")

    msg_id = update.message.reply_to_message.message_id

    if msg_id not in ADMIN_ROUTING:
        return await update.message.reply_text("Session expired")

    session = ADMIN_ROUTING[msg_id]
    user_id = session["user_id"]
    user_ctx = session["context"]

    price_text = "🎯 **Price List**\n━━━━━━━━━━━━━━━\n\n"

    for k, v in PRICES.items():
        price_text += f"💎 {k} = {v:,} MMK\n"

    price_text += (
        f"\n🎟 Weekly Pass = {PASS['weekly']:,} MMK"
        f"\n🎟 Twilight Pass = {PASS['twilight']:,} MMK\n\n"
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
        "🔍 Confirm Order\n"
        "━━━━━━━━━━━━━━━\n"
        f"{context.user_data['order']}\n"
        f"{context.user_data['amount']}\n\n"
        "YES ရိုက်ပါ"
    )

    return CONFIRM


# =========================
# CONFIRM
# =========================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":
        await update.message.reply_text(
            "💳 Payment Info\n\n"
            "KBZPay / Wave\n\n"
            f"{KPAY_NUMBER} ({KPAY_NAME})\n"
            f"{WAVE_NUMBER} ({WAVE_NAME})\n\n"
            "Screenshot ပို့ပါ"
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
# MAIN (FIXED FOR RENDER)
# =========================
def main():
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
    app.run_polling()


if __name__ == "__main__":
    main()
