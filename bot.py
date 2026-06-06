from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# ==========================================
# STATES
# ==========================================
GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# ==========================================
# START
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Order စတင်ပါ။")
    return GET_ORDER


# ==========================================
# ORDER
# ==========================================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"] = update.message.text
    await update.message.reply_text("💰 Amount ရိုက်ပါ")
    return GET_AMOUNT


# ==========================================
# AMOUNT
# ==========================================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    await update.message.reply_text("✅ Confirm လုပ်ပါ / ရေးပါ YES")
    return CONFIRM


# ==========================================
# CONFIRM
# ==========================================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    if text == "yes":
        await update.message.reply_text("📸 Payment screenshot ပို့ပါ")
        return WAIT_PAYMENT
    else:
        await update.message.reply_text("❌ Cancel လိုက်ပါပြီ")
        return ConversationHandler.END


# ==========================================
# PAYMENT (USER SEND PHOTO)
# ==========================================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    order = context.user_data.get("order")
    amount = context.user_data.get("amount")

    ADMIN_ID = 7488034821  # 🔴 မင်း Telegram ID ထည့်ပါ

    keyboard = [
        [
            InlineKeyboardButton("✅ APPROVE", callback_data=f"acc|{user.id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"rej|{user.id}")
        ]
    ]

    text = (
        f"🆕 ORDER NEW\n"
        f"👤 User: {user.id}\n"
        f"📦 Order: {order}\n"
        f"💰 Amount: {amount}"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("📨 Admin ကို ပို့ပြီးပါပြီ")
    return ConversationHandler.END


# ==========================================
# CALLBACK (ADMIN)
# ==========================================
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        action, uid = query.data.split("|")
        uid = int(uid)
    except:
        return

    # =========================
    if action == "acc":
        await context.bot.send_message(
            chat_id=uid,
            text="⏳ Payment approved!\n"
                 "Diamond ပို့နေပါပြီ..."
        )

        new_btn = [[
            InlineKeyboardButton("🚀 DIAMOND IN ACCOUNT (DONE)", callback_data=f"done|{uid}")
        ]]

        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(new_btn)
        )

    # =========================
    elif action == "rej":
        await context.bot.send_message(
            chat_id=uid,
            text="❌ Payment rejected\n"
                 "ပြေစာကို ပြန်စစ်ပါ"
        )

        restart_btn = [[
            InlineKeyboardButton("🔄 Restart", callback_data="restart")
        ]]

        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n❌ REJECTED",
            reply_markup=InlineKeyboardMarkup(restart_btn)
        )

    # =========================
    elif action == "done":
        await context.bot.send_message(
            chat_id=uid,
            text="💎 Diamonds are now in your account!\n"
                 "Pepe GameShop ကို ကျေးဇူးတင်ပါတယ် 🙏"
        )

        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n✅ DELIVERED",
            reply_markup=None
        )

    # =========================
    elif query.data == "restart":
        await query.message.reply_text("စတင်ရန် /start")


# ==========================================
# MAIN
# ==========================================
def main():
    TOKEN = "YOUR_BOT_TOKEN"

    if not TOKEN:
        print("BOT_TOKEN missing")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(callback))

    print("Bot running 24/7 🚀")
    app.run_polling()


if name == "__main__":
    main()
