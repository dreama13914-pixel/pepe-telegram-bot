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

# Global runtime dictionary to connect ongoing user sessions to Admin responses
# Key: User Chat ID -> Value: Conversation Context Tracker
ADMIN_ROUTING = {}

# ==========================================
# STATES
# ==========================================
# Added WAIT_ADMIN_PRICE state to hold the customer session
GET_ORDER, WAIT_ADMIN_PRICE, GET_AMOUNT, CONFIRM, WAIT_PAYMENT = range(5)

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
# STEP 1: USER SENDS ID -> INTERCEPT & ALERTS ADMIN
# ==========================================
async def handle_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id
    user_input = update.message.text
    
    context.user_data["order"] = user_input
    context.user_data["user_id"] = user_id

    # Alert the Admin immediately
    admin_alert = (
        f"🔍 **Incoming Server Verification Request**\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Customer: {user_id} (@{update.message.from_user.username or 'No Username'})\n"
        f"📝 Game ID Details: `{user_input}`\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💡 **Action Required:** Please check the server details. "
        f"Then, *Reply directly to this exact message* with the pricing list text or Server group instructions you want this user to see."
    )
    
    # Send to admin and store the message object ID to match the reply later
    admin_msg = await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_alert,
        parse_mode="Markdown"
    )
    
    # Register this cross-link session map globally
    ADMIN_ROUTING[admin_msg.message_id] = {
        "user_id": user_id,
        "context": context
    }

    # Inform the user they are placed in a short validation queue
    await update.message.reply_text(
        "⏳ ကျွန်ုပ်တို့၏ Admin မှ သင်၏ Server အား စစ်ဆေးနေပါသည်။\n"
        "ခေတ္တခဏ စောင့်ဆိုင်းပေးပါရန် မေတ္တာရပ်ခံအပ်ပါသည်။..."
    )
    
    return WAIT_ADMIN_PRICE


# ==========================================
# STEP 2: ADMIN HANDLES DIRECT TEXT ROUTING 
# ==========================================
async def handle_admin_pricing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ensure only the designated Admin can push price matrices
    if update.message.chat_id != ADMIN_ID:
        return

    # Check if the Admin replied to a message sent by the bot
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply directly to the specific user request alert message.")
        return

    replied_msg_id = update.message.reply_to_message.message_id
    
    if replied_msg_id not in ADMIN_ROUTING:
        await update.message.reply_text("⚠️ Session expired or invalid request mapping.")
        return

    # Retrieve user mapping target data
    session_data = ADMIN_ROUTING[replied_msg_id]
    target_user_id = session_data["user_id"]
    user_context = session_data["context"]
    
    # Get custom layout provided live by Admin
    admin_custom_prices = update.message.text
    user_context.user_data["custom_price_shown"] = admin_custom_prices

    # Send dynamic prices straight into customer window chat stream
    await context.bot.send_message(
        chat_id=target_user_id,
        text=(
            f"🎯 **Server Verification Complete**\n\n"
            f"{admin_custom_prices}\n\n"
            f"💰 ဝယ်ယူမည့် ပမာဏ သို့မဟုတ် Pass အမျိုးအစားကို ရေးပေးပါ။"
        )
    )

    # Clean up reference mapping
    del ADMIN_ROUTING[replied_msg_id]

    # Advance the specific user's conversation step programmatically
    # We update the internal active state machine tracker for that user instance
    user_context.user_data[ConversationHandler.class_key(ConversationHandler)] = GET_AMOUNT
    
    await update.message.reply_text(f"✅ Price list pushed successfully to User {target_user_id}.")


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
    amount_info = "Diamonds"
    
    for line in caption_lines:
        if "Amount Sent:" in line:
            amount_info = line.replace("💰 Amount Sent:", "").strip()

    if action == "acc":
        await context.bot.send_message(
            chat_id=uid,
            text=f"⏳ Payment approved!\nDiamond ({amount_info}) ပို့နေပါပြီ..."
        )

        new_btn = [[
            InlineKeyboardButton("🚀 DIAMOND IN ACCOUNT (DONE)", callback_data=f"done|{uid}")
        ]]

        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\nPAYMENT APPROVED ✅\n(Sending Diamonds...)",
            reply_markup=InlineKeyboardMarkup(new_btn)
        )

    elif action == "rej":
        await context.bot.send_message(
            chat_id=uid,
            text="❌ ငွေလွှဲမအောင်မြင်ပါ\nပြေစာကို ပြန်လည်စစ်ဆေးပေးပါ။"
        )

        restart_btn = [[
            InlineKeyboardButton("🔄 Restart", callback_data="restart")
        ]]

        await query.edit_message_caption(
            caption=(query.message.caption or "") + "\n\n❌ REJECTED",
            reply_markup=InlineKeyboardMarkup(restart_btn)
        )

    elif action == "done":
        await context.bot.send_message(
            chat_id=uid,
            text=f"💎 **Diamonds are now in your account!**\n\n"
                 f"လူကြီးမင်း၏ Account ထဲသို့ Diamond ({amount_info}) များ ထည့်ပေးပြီးပါပြီ။ ✨\n"
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
            # User remains trapped here while you look up prices
            WAIT_ADMIN_PRICE: [MessageHandler(filters.ALL, lambda u, c: None)], 
            GET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount)],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
            WAIT_PAYMENT: [MessageHandler(filters.PHOTO, payment)],
        },
        fallbacks=[CommandHandler("start", start)]
    )

    app.add_handler(conv)
    
    # Handler for Admin text replies to intercept pricing delivery
    app.add_handler(MessageHandler(
        filters.Chat(ADMIN_ID) & filters.TEXT & ~filters.COMMAND, 
        handle_admin_pricing
    ))
    
    app.add_handler(CallbackQueryHandler(callback))

    print("Bot running with Manual Admin Verification routing 🚀")
    
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
