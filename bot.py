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

TOKEN = os.getenv("BOT_TOKEN") 

ADMIN_ID = 7488034821           
KPAY_NUMBER = "09401878226"     
KPAY_NAME = "Li Li Naing"       
WAVE_NUMBER = "09401878226"     
WAVE_NAME = "Li Li Naing"       
TIMEZONE = pytz.timezone('Asia/Yangon')

# 💎 UPDATED PRICES (+300 MMK FIX)
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
    
    await context.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=photo,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    await update.message.reply_text("Admin မှ ပြေစာကို စစ်ဆေးနေပါတယ်။ ခေတ္တစောင့်ဆိုင်းပေးပါ။")
    return ConversationHandler.END

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("|")
    uid = int(uid)

    if action == "acc":
        await context.bot.send_message(chat_id=uid, text="ငွေလွှဲမှု အောင်မြင်ပါတယ်။ Diamond ပို့ဆောင်နေပါပြီ။ ✅")
        await query.edit_message_caption(query.message.caption + "\n\nStatus: [APPROVED ✅]")
    elif action == "rej":
        await context.bot.send_message(chat_id=uid, text="ငွေလွှဲမှု မအောင်မြင်ပါ။ ပြေစာပြန်စစ်ပါ။ ❌")
        await query.edit_message_caption(query.message.caption + "\n\nStatus: [REJECTED ❌]")

async def user_restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("စတင်ရန် /start ကို နှိပ်ပေးပါ။")

# ==========================================
# 🚀 START BOT (FIXED FOR RENDER)
# ==========================================

if __name__ == '__main__':
    if not TOKEN:
        print("⚠️ BOT_TOKEN မထည့်ထားပါ (Render Environment Variables စစ်ပါ)")
        TOKEN = "DUMMY_TOKEN"

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
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^(acc|rej)$"))
    app.add_handler(CallbackQueryHandler(user_restart, pattern="^user_restart$"))
    
    print("Pepe Shop is LIVE 24/7!")
    app.run_polling()
