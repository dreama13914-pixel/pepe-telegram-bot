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

GET_ID, GET_SERVER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

KBZPAY = "09401878226"
WAVEPAY = "09788599697"
SG_EXTRA = 2900

SHOP_TZ = pytz.timezone("Asia/Yangon")

# =========================
# PRICE LIST (YOUR EXACT STYLE)
# =========================

PRICE_TEXT = """💎 Diamond ဈေးများ

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

🎟 Weekly Pass 1 = 6,550 MMK
🎟 Weekly Pass 2 = 13,100 MMK
🎟 Weekly Pass 3 = 19,650 MMK
🎟 Twilight Pass = 35,050 MMK
"""

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
# STATE STORAGE
# =========================

user_data_store = {}

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👋 Hello!\n"
        "🎮 Welcome to Pepe's Diamond Shop\n\n"
        "📌 သင့် Game ID ကိုပို့ပါ\n"
        "👉 ဥပမာ - Pepe 1600113465 (16740)"
    )

    return GET_ID


# =========================
# USER SEND ID
# =========================

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    user_data_store[user_id] = {
        "id_text": update.message.text
    }

    keyboard = [
        [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"mm_{user_id}")],
        [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"sg_{user_id}")],
        [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{user_id}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        f"🔍 NEW ID CHECK\n{update.message.text}\nUSER: {user_id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("⏳ Admin စစ်ဆေးနေပါသည်...")
    return GET_SERVER


# =========================
# ADMIN SERVER BUTTONS
# =========================

async def server_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "ban":
        await context.bot.send_message(uid, "❌ သင့် Order ကို ပယ်ဖျက်လိုက်ပါသည်")
        return

    user_data_store[uid]["server"] = action

    await context.bot.send_message(
        uid,
        f"🎯 Server Confirmed: {action.upper()}\n\n"
        f"{PRICE_TEXT}\n\n"
        "💎 အရေအတွက် ရိုက်ပါ (ဥပမာ 55, 86, weekly1)"
    )

    return GET_AMOUNT


# =========================
# AMOUNT
# =========================

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id
    text = update.message.text.lower().strip()

    data = user_data_store.get(user_id)

    if not data:
        await update.message.reply_text("❌ /start ပြန်လုပ်ပါ")
        return ConversationHandler.END

    try:
        value = int(text)
    except:
        value = text

    price = None

    if isinstance(value, int) and value in BASE_PRICES:
        price = BASE_PRICES[value]
    elif isinstance(value, str) and value in PASS_PRICES:
        price = PASS_PRICES[value]

    if price is None:
        await update.message.reply_text("❌ မရှိပါ ပြန်ရိုက်ပါ")
        return GET_AMOUNT

    if data["server"] == "sg":
        price += SG_EXTRA

    data["amount"] = value
    data["price"] = price

    await update.message.reply_text(
        f"🔍 CONFIRM ORDER\n\n"
        f"📦 Item: {value}\n"
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
        f"💳 PAYMENT INFO\n\n"
        f"KBZPay: {KBZPAY}\n"
        f"WavePay: {WAVEPAY}\n\n"
        "📸 Screenshot ပို့ပါ"
    )

    return WAIT_PAYMENT


# =========================
# PAYMENT → ADMIN
# =========================

async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_chat.id

    keyboard = [
        [InlineKeyboardButton("✅ ACCEPT", callback_data=f"acc_{user_id}")],
        [InlineKeyboardButton("❌ REJECT", callback_data=f"rej_{user_id}")]
    ]

    await context.bot.send_message(
        ADMIN_ID,
        "💰 NEW PAYMENT RECEIVED",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await context.bot.forward_message(
        ADMIN_ID,
        user_id,
        update.message.message_id
    )

    await update.message.reply_text("⏳ Admin စစ်ဆေးနေပါသည်...")
    return ConversationHandler.END


# =========================
# ADMIN FINAL ACTION
# =========================

async def admin_final(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "rej":
        await context.bot.send_message(
            uid,
            "❌ ငွေလက်ခံမရသေးပါ\n👉 ပြန်စပြီးကြိုးစားပါ"
        )
        return

    if action == "acc":
        await context.bot.send_message(
            uid,
            "⏳ Diamonds ထည့်နေပါသည်...\nAdmin လုပ်ဆောင်နေသည်"
        )

        # second button (finish)
        await context.bot.send_message(
            ADMIN_ID,
            f"👤 User {uid} accepted\n"
            "ပြီးပါက FINISH နှိပ်ပါ",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏁 FINISH", callback_data=f"fin_{uid}")]
            ])
        )


async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    _, uid = query.data.split("_")
    uid = int(uid)

    await context.bot.send_message(
        uid,
        "🎉 Diamonds သင့်အကောင့်ထဲထည့်ပြီးပါပြီ\n"
        "🙏 ကျေးဇူးတင်ပါတယ်"
    )


# =========================
# MAIN (SAFE FOR RENDER)
# =========================

def main():

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GET_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_id)],
            GET_SERVER: [CallbackQueryHandler(server_buttons)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(admin_final, pattern="^(acc|rej)_"))
    app.add_handler(CallbackQueryHandler(finish, pattern="^fin_"))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
