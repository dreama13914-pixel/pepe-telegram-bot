import os
import asyncio
from datetime import datetime
import pytz 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# ==========================================
# ⚙️ CONFIGURATION & PRICE LIST
# ==========================================
ADMIN_ID = 7488034821  
KPAY_NUMBER = "09401878226"     
KPAY_NAME = "Li Li Naing"       
WAVE_NUMBER = "09788599697"     
WAVE_NAME = "Li Li Naing"       
TIMEZONE = pytz.timezone('Asia/Yangon')

PRICES = """
💎 **Diamond ဈေးနှုန်းများ**
❗️Minimum order = 55 💎

💎 55 = 5,100 MMK
💎 86 = 5,600 MMK
💎 165 = 14,600 MMK
💎 172 = 15,300 MMK
💎 257 = 22,600 MMK
💎 275 = 24,100 MMK
💎 343 = 30,300 MMK
💎 565 = 49,100 MMK
💎 706 = 61,300 MMK
💎 2195 = 189,300 MMK
💎 3688 = 317,600 MMK
💎 5532 = 476,200 MMK
💎 9288 = 799,300 MMK

🎟 Weekly Pass = 6,800 MMK
🎟 Twilight Pass = 35,300 MMK
"""

# ==========================================
# STATES
# ==========================================
GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# ==========================================
# START
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Pepe GameShop မှ ကြိုဆိုပါတယ်။ 🎮\n\n"
        "Diamond ဝယ်ယူရန်အတွက် သင်၏ Name နှင့် ID (Zone) ကို ပို့ပေးပါ။\n"
        "ဥပမာ - Pepe 123456789 (1234)"
    )
    return GET_ORDER


# ==========================================
# ORDER
# ==========================================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["order"] = update.message.text
    await update.message.reply_text(f"{PRICES}\n\n💰 ဝယ်ယူမည့် ပမာဏ သို့မဟုတ် Pass အမျိုးအစားကို ရေးပေးပါ။")
    return GET_AMOUNT


# ==========================================
# AMOUNT
# ==========================================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    
    recheck_text = (
        "🔍 **အချက်အလက်များကို ပြန်လည်စစ်ဆေးပေးပါ**\n\n"
        f"📝 ID/Name: {context.user_data['order']}\n"
        f"💎 Amount: {context.user_data['amount']}\n\n"
        "အထက်ပါ အချက်အလက်များ မှန်ကန်ပါက 'YES' ဟု စာရိုက်ပြီး ပို့ပေးပါ။"
    )
    await update.message.reply_text(recheck_text)
    return CONFIRM


# ==========================================
# CONFIRM
# ==========================================
async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower().strip()

    if text == "yes":
        payment_text = (
            "💳 **Payment Info**\n\n"
            "**[ KBZPay ]**\n"
            f"Kpay - {KPAY_NUMBER}\n"
            f"Name - {KPAY_NAME}\n\n"
            "**[ Wave Money ]**\n"
            f"Wave - {WAVE_NUMBER}\n"
            f"Name - {WAVE_NAME}\n\n"
            "ငွေလွှဲပြီးပါက ပြေစာ (Screenshot) ကို ပုံအဖြစ် ပို့ပေးပါ။"
        )
        await update.message.reply_text(payment_text, parse_mode="Markdown")
        return WAIT_PAYMENT
    else:
        await update.message.reply_text("❌ Cancel လိုက်ပါပြီ။ စတင်ရန် /start ကို ပြန်နှိပ်ပါ။")
        return ConversationHandler.END


# ==========================================
# PAYMENT (USER SEND PHOTO)
# ==========================================
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    order = context.user_data.get("order")
    amount = context.user_data.get("amount")

    keyboard = [
        [
            InlineKeyboardButton("✅ APPROVE", callback_data=f"acc|{user.id}"),
            InlineKeyboardButton("❌ REJECT", callback_data=f"rej|{user.id}")
        ]
    ]

    text = (
        f"🆕 ORDER NEW\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👤 User: {user.id} (@{user.username if user.username else user.first_name})\n"
        f"📦 Info: {order}\n"
        f"💰 Amount: {amount}\n"
        f"━━━━━━━━━━━━━━━"
    )

    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    await update.message.reply_text("📨 ပြေစာပို့ပြီးပါပြီ။ Admin စစ်ဆေးနေပါသဖြင့် ခေတ္တစောင့်ဆိုင်းပေးပါ။")
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
        if query.data == "restart":
            await query.message.reply_text("စတင်ရန် /start")
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

        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\nPAYMENT APPROVED ✅\n(Sending Diamonds...)",
            reply_markup=InlineKeyboardMarkup(new_btn)
        )

    # =========================
    elif action == "rej":
        await context.bot.send_message(
            chat_id=uid,
            text="❌ ငွေလွှဲမအောင်မြင်ပါ\n"
                 "ပြေစာကို ပြန်လည်စစ်ဆေးပေးပါ။"
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
            text="💎 **Diamonds are now in your account!**\n\n"
                 "လူကြီးမင်း၏ အကောင့်ထဲသို့ Diamond များ ထည့်ပေးပြီးပါပြီ။ ✨\n"
                 "Pepe GameShop ကို အားပေးမှုအတွက် အထူးကျေးဇူးတင်ရှိပါသည်။ 🙏"
        )

        clean_caption = (query.message.caption or "").replace("\n(Sending Diamonds...)", "")
        await query.edit_message_caption(
            caption=clean_caption + "\n\n✅ DELIVERED & SUCCESS",
            reply_markup=None
        )


# ==========================================
# 🚀 MAIN (UPDATED FOR PYTHON 3.14+)
# ==========================================
async def async_main():
    TOKEN = os.getenv("BOT_TOKEN")

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
    
    # Initialize and spin up the polling context smoothly
    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    
    # Keep the async context alive cleanly on Render
    while True:
        await asyncio.sleep(3600)


def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")


if __name__ == "__main__":
    main()
