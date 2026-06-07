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
GET_ORDER, WAIT_ADMIN_PRICE, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

# =========================
# START (MYANMAR RESTORED)
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)

    if not (12 <= now.hour < 19):
        await update.message.reply_text(
            "🌙 **Pepe GameShop ပိတ်ထားပါသည်။**\n\n"
            "ဖွင့်ချိန် - နေ့လည် 12:00 PM မှ ညနေ 7:00 PM ထိ\n"
            "အချိန်ပြန်ရောက်မှ ပြန်လာပေးပါ။ 🙏"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎮 **Pepe GameShop မှ ကြိုဆိုပါတယ်။**\n\n"
        "💡 သင်၏ Game ID ပို့ပေးပါ\n"
        "ဥပမာ - Pepe 123456 (7788)\n\n"
        "⏳ Server စစ်ဆေးပြီးနောက် စျေးနှုန်းပို့ပေးပါမည်။"
    )
    return GET_ORDER


# =========================
# USER ORDER (MYANMAR)
# =========================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    text = update.message.text.strip()

    context.user_data["order"] = text
    context.user_data["user_id"] = user_id

    admin_msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "🔍 **SERVER စစ်ဆေးရန် တောင်းဆိုမှု**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User: {user_id}\n"
            f"📝 Input: {text}\n\n"
            "👉 အောက်ပါပုံစံဖြင့် reply ပြန်ပါ\n"
            "server: xxx\n"
            "zone: xxx\n"
            "mm: xxx\n"
            "sg: xxx"
        )
    )

    ADMIN_ROUTING[admin_msg.message_id] = {
        "user_id": user_id,
        "context": context
    }

    await update.message.reply_text(
        "⏳ Server စစ်ဆေးနေပါသည်...\nခဏစောင့်ပေးပါ။"
    )

    return WAIT_ADMIN_PRICE


# =========================
# ADMIN PARSER
# =========================
def parse_admin(text: str):
    data = {
        "server": "မရှိပါ",
        "zone": "မရှိပါ",
        "mm": "မရှိပါ",
        "sg": "မရှိပါ"
    }

    for line in text.lower().split("\n"):
        if "server:" in line:
            data["server"] = line.split("server:")[1].strip()
        elif "zone:" in line:
            data["zone"] = line.split("zone:")[1].strip()
        elif "mm:" in line:
            data["mm"] = line.split("mm:")[1].strip()
        elif "sg:" in line:
            data["sg"] = line.split("sg:")[1].strip()

    return data


# =========================
# ADMIN HANDLER (MYANMAR OUTPUT)
# =========================
async def handle_admin_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != ADMIN_ID:
        return

    if not update.message.reply_to_message:
        return await update.message.reply_text("Reply ပြန်ပြီးမှ အသုံးပြုပါ။")

    msg_id = update.message.reply_to_message.message_id

    if msg_id not in ADMIN_ROUTING:
        return await update.message.reply_text("Session မရှိတော့ပါ။")

    session = ADMIN_ROUTING[msg_id]
    user_id = session["user_id"]
    user_ctx = session["context"]

    data = parse_admin(update.message.text)

    price_text = (
        "🎯 **Server စစ်ဆေးပြီးပါပြီ**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 Server: {data['server']}\n"
        f"🌐 Zone: {data['zone']}\n\n"
        "💰 **စျေးနှုန်းများ**\n"
        f"🇲🇲 Myanmar: {data['mm']}\n"
        f"🇸🇬 Singapore: {data['sg']}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "💎 ဝယ်ယူလိုသော ပမာဏကို ရေးပေးပါ"
    )

    await context.bot.send_message(chat_id=user_id, text=price_text)

    del ADMIN_ROUTING[msg_id]

    user_ctx.user_data["flow"] = GET_AMOUNT

    await update.message.reply_text("✅ User ကို စျေးနှုန်းပို့ပြီးပါပြီ။")


# =========================
# AMOUNT (MYANMAR)
# =========================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("flow") != GET_AMOUNT:
        return

    context.user_data["amount"] = update.message.text

    await update.message.reply_text(
        "🔍 **အချက်အလက် စစ်ဆေးရန်**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Order: {context.user_data['order']}\n"
        f"💎 Amount: {context.user_data['amount']}\n"
        "━━━━━━━━━━━━━━━━━━━\n\n"
        "အတည်ပြုရန် YES ရိုက်ပို့ပါ"
    )

    return CONFIRM


# =========================
# CONFIRM (MYANMAR)
# =========================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.text.lower() == "yes":
        await update.message.reply_text(
            "💳 **ငွေပေးချေမှု အချက်အလက်များ**\n\n"
            "🏦 KBZPay\n"
            f"နံပါတ်: {KPAY_NUMBER}\n"
            f"နာမည်: {KPAY_NAME}\n\n"
            "💸 Wave Money\n"
            f"နံပါတ်: {WAVE_NUMBER}\n"
            f"နာမည်: {WAVE_NAME}\n\n"
            "📸 ငွေလွှဲပြီးပါက Screenshot ပို့ပေးပါ"
        )
        return WAIT_PAYMENT

    await update.message.reply_text("❌ ပယ်ဖျက်လိုက်ပါသည်။")
    return ConversationHandler.END


# =========================
# PAYMENT
# =========================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    keyboard = [[
        InlineKeyboardButton("✅ အတည်ပြု", callback_data=f"acc|{user.id}"),
        InlineKeyboardButton("❌ ငြင်းပယ်", callback_data=f"rej|{user.id}")
    ]]

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=(
            "🆕 **အော်ဒါအသစ်**\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            f"👤 User: {user.id}\n"
            f"📦 Order: {context.user_data.get('order')}\n"
            f"💎 Amount: {context.user_data.get('amount')}\n"
            "━━━━━━━━━━━━━━━━━━━"
        ),
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("📨 Admin ကိုပို့ပြီးပါပြီ။")
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
        await context.bot.send_message(
            uid,
            "⏳ အတည်ပြုထားပါသည်။ Diamonds ပို့နေပါသည်..."
        )
    else:
        await context.bot.send_message(
            uid,
            "❌ ငွေပေးချေမှု မအောင်မြင်ပါ"
        )


# =========================
# MAIN
# =========================
async def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ORDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order)],
            WAIT_ADMIN_PRICE: [MessageHandler(filters.TEXT, lambda u, c: None)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Chat(ADMIN_ID) & filters.TEXT, handle_admin_pricing))
    app.add_handler(CallbackQueryHandler(callback))

    print("BOT RUNNING 🚀")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main())
