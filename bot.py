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
# ⚙️ CONFIGURATION & TIMEZONE
# ==========================================
ADMIN_ID = 7488034821  
KPAY_NUMBER = "09401878226"     
KPAY_NAME = "Li Li Naing"       
WAVE_NUMBER = "09788599697"     
WAVE_NAME = "Li Li Naing"       
TIMEZONE = pytz.timezone('Asia/Yangon')

# 🚫 BANNED SERVER IDS (Add any 4-digit server codes you want to block here)
BANNED_SERVERS = ["5001", "5002", "5003", "9999"]

# ==========================================
# 💰 DYNAMIC PRICE LISTS
# ==========================================
# Normal Servers (-50 MMK discount applied)
NORMAL_PRICES = """
🇲🇲 **Normal Server ဈေးနှုန်းများ (-50 MMK Discount!)**
❗️Minimum order = 55 💎

💎 55 = 5,050 MMK
💎 86 = 5,550 MMK
💎 165 = 14,550 MMK
💎 172 = 15,250 MMK
💎 257 = 22,550 MMK
💎 275 = 24,050 MMK
💎 343 = 30,250 MMK
💎 565 = 49,050 MMK
💎 706 = 61,250 MMK
💎 2195 = 189,250 MMK
💎 3688 = 317,550 MMK
💎 5532 = 476,150 MMK
💎 9288 = 799,250 MMK

🎟 Weekly Pass = 6,750 MMK
🎟 Twilight Pass = 35,250 MMK
"""

# Singapore Servers (+2,900 MMK premium added)
SG_PRICES = """
🇸🇬 **Singapore Server ဈေးနှုန်းများ (+2,900 MMK Group)**
❗️Minimum order = 55 💎

💎 55 = 8,000 MMK
💎 86 = 8,500 MMK
💎 165 = 17,500 MMK
💎 172 = 18,200 MMK
💎 257 = 25,500 MMK
💎 275 = 27,000 MMK
💎 343 = 33,200 MMK
💎 565 = 52,000 MMK
💎 706 = 64,200 MMK
💎 2195 = 192,200 MMK
💎 3688 = 320,500 MMK
💎 5532 = 479,100 MMK
💎 9288 = 802,200 MMK

🎟 Weekly Pass = 9,700 MMK
🎟 Twilight Pass = 38,200 MMK
"""

# ==========================================
# STATES
# ==========================================
GET_ORDER, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(4)

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def extract_server(text):
    """Extracts a 4-digit server number from brackets like (1234) or plain text"""
    import re
    match = re.search(r'\((\d{4})\)', text)
    if match:
        return match.group(1)
    match_alt = re.search(r'\b\d{4}\b', text)
    if match_alt:
        return match_alt.group(0)
    return "Unknown"

def is_singapore_server(server_id):
    """Checks if server belongs to Singapore range (starts with 2)"""
    if server_id.isdigit() and server_id.startswith('2'):
        return True
    return False

# ==========================================
# START (SHOP HOURS: 12 PM - 7 PM)
# ==========================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now(TIMEZONE)
    current_hour = now.hour

    if not (12 <= current_hour < 19):
        await update.message.reply_text(
            "🌙 **Pepe GameShop is currently CLOSED.**\n\n"
            "ကျွန်ုပ်တို့၏ ဆိုင်ဖွင့်ချိန်မှာ မနက် 12:00 PM မှ ညနေ 7:00 PM အထိ ဖြစ်ပါတယ်။\n"
            "ဖွင့်ချိန်ရောက်မှ ပြန်လာခဲ့ပေးပါ။ ကျေးဇူးတင်ပါတယ်။"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Pepe GameShop မှ ကြိုဆိုပါတယ်။ 🎮\n\n"
        "Diamond ဝယ်ယူရန်အတွက် သင်၏ Name နှင့် ID (Zone) ကို ပို့ပေးပါ။\n"
        "ဥပမာ - Pepe 123456789 (1234)"
    )
    return GET_ORDER


# ==========================================
# ORDER (WITH AUTO BANNED-SERVER DISMISSAL)
# ==========================================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    context.user_data["order"] = user_input
    
    server_id = extract_server(user_input)
    context.user_data["server_id"] = server_id
    
    # 🚫 Check if it's a banned server profile right away
    if server_id in BANNED_SERVERS:
        await update.message.reply_text(
            f"⚠️ **Top-up Failed (Banned Server Detected)**\n\n"
            f"လူကြီးမင်းပေးပို့ထားသော Server ID ({server_id}) သည် Myanmar Region တွင် "
            f"ငွေဖြည့်၍မရသော Ban Server ဖြစ်နေပါသဖြင့် စိတ်မကောင်းပါဘူးခင်ဗျာ။\n\n"
            f"ကျေးဇူးပြု၍ တရားဝင်အသုံးပြုနိုင်သော Server အကောင့်ဖြင့် ပြန်လည်စမ်းသပ်ပေးပါ။"
        )
        return ConversationHandler.END

    # 🇸🇬 Check if it belongs to Singapore premium range
    if is_singapore_server(server_id):
        context.user_data["server_type"] = "Singapore 🇸🇬"
        assigned_prices = SG_PRICES
        server_notice = f"Your profile is on **Server {server_id} (Singapore Server)**. The regional price has changed to match Singapore tiers."
    else:
        context.user_data["server_type"] = "Normal 🇲🇲"
        assigned_prices = NORMAL_PRICES
        server_notice = f"Your profile is on **Server {server_id} (Normal Server)**. Standard local prices apply."

    await update.message.reply_text(
        f"🎯 **Server Identification Success**\n"
        f"ℹ️ {server_notice}\n\n"
        f"{assigned_prices}\n\n"
        f"💰 ဝယ်ယူမည့် ပမာဏ သို့မဟုတ် Pass အမျိုးအစားကို ရေးပေးပါ။"
    )
    return GET_AMOUNT


# ==========================================
# AMOUNT
# ==========================================
async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["amount"] = update.message.text
    
    recheck_text = (
        "🔍 **အချက်အလက်များကို ပြန်လည်စစ်ဆေးပေးပါ**\n\n"
        f"📝 ID/Name: {context.user_data['order']}\n"
        f"🌐 Region Group: {context.user_data['server_type']} (Server {context.user_data['server_id']})\n"
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
    server_id = context.user_data.get("server_id")
    server_type = context.user_data.get("server_type")

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
        f"🌐 Server Config: {server_id} ({server_type})\n"
        f"💰 Amount Sent: {amount}\n"
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
# CALLBACK (ADMIN ACTIONS)
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

    caption_lines = query.message.caption.split("\n")
    server_info = "Normal Server"
    amount_info = "Diamonds"
    
    for line in caption_lines:
        if "Server Config:" in line:
            server_info = line.replace("🌐 Server Config:", "").strip()
        if "Amount Sent:" in line:
            amount_info = line.replace("💰 Amount Sent:", "").strip()

    # =========================
    if action == "acc":
        await context.bot.send_message(
            chat_id=uid,
            text=f"⏳ Payment approved for **Server {server_info}**!\n"
                 f"Diamond ({amount_info}) ပို့နေပါပြီ..."
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
            text=f"💎 **Diamonds are now in your account!**\n\n"
                 f"လူကြီးမင်း၏ **Server {server_info}** ထဲသို့ Diamond ({amount_info}) များ ထည့်ပေးပြီးပါပြီ။ ✨\n"
                 f"Pepe GameShop ကို အားပေးမှုအတွက် အထူးကျေးဇူးတင်ရှိပါသည်။ 🙏"
        )

        clean_caption = (query.message.caption or "").replace("\n(Sending Diamonds...)", "")
        await query.edit_message_caption(
            caption=clean_caption + "\n\n✅ DELIVERED & SUCCESS",
            reply_markup=None
        )


# ==========================================
# 🚀 MAIN RUNNER
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
    
    await app.initialize()
    await app.updater.start_polling()
    await app.start()
    
    while True:
        await asyncio.sleep(3600)


def main():
    try:
        asyncio.run(async_main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")


if __name__ == "__main__":
    main()
