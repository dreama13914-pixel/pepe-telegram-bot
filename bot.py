import re
import os
from datetime import datetime
import pytz 
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
TOKEN = os.getenv("8769310147:AAG00L7p6dbVA8SrWIl7S-rndTuu3c9ou40") 

# 🛠️ CHANGE THESE VALUES TO YOUR OWN:
ADMIN_ID = 7488034821           # 👈 Replace with your real Telegram User ID
KPAY_NUMBER = "09401878226"     # 👈 Replace with your Kpay Phone Number
KPAY_NAME = "Li Li Naing"       # 👈 Replace with your Kpay Account Name

WAVE_NUMBER = "09401878226"     # 👈 Put your Wave Pay Phone Number here
WAVE_NAME = "Li Li Naing"       # 👈 Put your Wave Pay Account Name here

TIMEZONE = pytz.timezone('Asia/Yangon')

# 💎 EDIT YOUR PRICES HERE IF THEY CHANGE:
PRICES = """
💎 **Diamond ဈေးနှုန်းများ**
❗️Minimum order = 55 💎

💎 55 = 4,800 MMK
💎 86 = 5,300 MMK
💎 165 = 14,300 MMK
💎 172 = 15,000 MMK
💎 257 = 22,300 MMK
💎 275 = 23,800 MMK
💎 343 = 30,000 MMK
💎 565 = 48,800 MMK
💎 706 = 61,000 MMK
💎 2195 = 189,000 MMK
💎 3688 = 317,300 MMK
💎 5532 = 475,900 MMK
💎 9288 = 799,000 MMK

🎟 Weekly Pass = 6,500 MMK
🎟 Twilight Pass = 35,000 MMK
"""

GET_ORDER_INFO, GET_AMOUNT, CONFIRM_ALL, WAIT_PAYMENT = range(4)

# ==========================================
# 🤖 BOT HANDLERS
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)
    current_hour = now.hour

    if not (11 <= current_hour < 17):
        await update.message.reply_text(
            "🌙 **Pepe GameShop is currently CLOSED.**\n\n"
            "ကျွန်ုပ်တို့၏ ဆိုင်ဖွင့်ချိန်မှာ မနက် 11:00 AM မှ ညနေ 5:00 PM အထိ ဖြစ်ပါတယ်။\n"
            "ဖွင့်ချိန်ရောက်မှ ပြန်လာခဲ့ပေးပါ။ ကျေးဇူးတင်ပါတယ်။"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Pepe GameShop မှ ကြိုဆိုပါတယ်။ 🎮\n\n"
        "Diamond ဝယ်ယူရန်အတွက် သင်၏ **Name** နှင့် **ID (Zone)** ကို ပို့ပေးပါ။\n"
        "ဥပမာ - Pepe 123456789 (1234)"
    )
    return GET_ORDER_INFO

async def handle_order_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['order_details'] = update.message.text
    await update.message.reply_text(f"{PRICES}\nဝယ်ယူမည့် ပမာဏ သို့မဟုတ် Pass အမျိုးအစားကို ရေးပေးပါ။")
    return GET_AMOUNT

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['amount'] = update.message.text
    
    recheck_text = (
        "🔍 **အချက်အလက်များကို ပြန်လည်စစ်ဆေးပေးပါ**\n\n"
        f"📝 ID/Name: {context.user_data['order_details']}\n"
        f"💎 Amount: {context.user_data['amount']}\n\n"
        "အထက်ပါ အချက်အလက်များ မှန်ကန်ပါသလား?"
    )
    
    kb = [["Yes", "No"]]
    await update.message.reply_text(
        recheck_text,
        reply_markup=ReplyKeyboardMarkup(kb, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_ALL

async def confirm_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Yes":
        payment_text = (
            "💳 **Payment Info**\n\n"
            "**[ KBZPay ]**\n"
            f"Kpay - {KPAY_NUMBER}\n"
            f"Name - {KPAY_NAME}\n\n"
            "**[ Wave Money ]**\n"
            f"Wave - {WAVE_NUMBER}\n"
            f"Name - {WAVE_NAME}\n\n"
            "ငွေလွှဲပြီးပါက ပြေစာ (Screenshot) ပို့ပေးပါ။"
        )
        await update.message.reply_text(payment_text, parse_mode="Markdown")
        return WAIT_PAYMENT
    else:
        await update.message.reply_text("အချက်အလက်များ မှားယွင်းပါက /start ကိုနှိပ်ပြီး ပြန်လည်စတင်ပါ။")
        return ConversationHandler.END

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = context.user_data
    
    if not update.message.photo:
        await update.message.reply_text("ကျေးဇူးပြု၍ ငွေလွှဲပြေစာ Screenshot ပုံပို့ပေးပါ။")
        return WAIT_PAYMENT

    photo = update.message.photo[-1].file_id
    caption = (
        f"📦 **New Order Received!**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📝 Info: {data.get('order_details')}\n"
        f"💎 Amount: {data.get('amount')}\n"
        f"👤 From: @{user.username if user.username else user.first_name}\n"
        f"━━━━━━━━━━━━━━━"
    )
    
    buttons = [
        [InlineKeyboardButton("✅ Accept Payment", callback_data=f"acc|{user.id}")],
        [InlineKeyboardButton("❌ Reject Payment", callback_data=f"rej|{user.id}")]
    ]
    
    await context.bot.send_photo(chat_id=ADMIN_ID, photo=photo, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    await update.message.reply_text("Admin မှ ပြေစာကို စစ်ဆေးနေပါတယ်။ ခေတ္တစောင့်ဆိုင်းပေးပါ။")
    return ConversationHandler.END

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, uid = query.data.split("|")
    if action == "acc":
        await context.bot.send_message(uid, "ငွေလွှဲမှု အောင်မြင်ပါတယ်။ Diamond ပို့ဆောင်ပေးနေပြီဖြစ်လို့ ၃ မိနစ်လောက်စောင့်ပေးပါ။ ⏳")
        new_buttons = [[InlineKeyboardButton("🚀 Mark as Success", callback_data=f"done|{uid}")]]
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(new_buttons))
    elif action == "rej":
        restart_btn = [[InlineKeyboardButton("🔄 Restart Process", callback_data="user_restart")]]
        await context.bot.send_message(uid, "ငွေလွှဲမှု မအောင်မြင်ပါ။ ပြေစာ ပြန်လည်စစ်ဆေးပေးပါ။ ❌", reply_markup=InlineKeyboardMarkup(restart_btn))
        await query.edit_message_caption(query.message.caption + "\n\nStatus: [REJECTED ❌]")
    elif action == "done":
        await context.bot.send_message(uid, "သင်ဝယ်ယူထားသော Diamond များ ပို့ဆောင်ပြီးပါပြီ။ ကျေးဇူးတင်ပါတယ်။ ✅")
        await query.edit_message_caption(query.message.caption + "\n\nStatus: [SUCCESS ✅]")

async def user_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("စတင်ရန် /start ကို နှိပ်ပေးပါ။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GET_ORDER_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_order_info)],
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM_ALL: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_all)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, handle_payment)],
        },
        fallbacks=[CommandHandler('start', start)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(acc|rej|done)"))
    app.add_handler(CallbackQueryHandler(user_restart, pattern="^user_restart$"))
    
    print("Pepe Shop is LIVE 24/7!")
    app.run_polling()
