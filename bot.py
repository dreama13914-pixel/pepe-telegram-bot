import os
from datetime import datetime
import pytz

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, CallbackQueryHandler, filters
)

# ================= CONFIG =================

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
BOT_TOKEN = os.getenv("BOT_TOKEN")

STATE_IDLE = "IDLE"
STATE_GET_ID = "GET_ID"
STATE_GET_SERVER = "GET_SERVER"
STATE_GET_AMOUNT = "GET_AMOUNT"
STATE_CONFIRM = "CONFIRM"
STATE_WAIT_PAYMENT = "WAIT_PAYMENT"

KBZPAY = "09401878226"
WAVEPAY = "09788599697"
SG_EXTRA = 2900

SHOP_TZ = pytz.timezone("Asia/Yangon")

# ================= SHOP TIME =================

def shop_open():
    now_mm = datetime.now(SHOP_TZ)
    minutes = now_mm.hour * 60 + now_mm.minute
    return 11 * 60 <= minutes <= 19 * 60 + 30


# ================= PRICE LIST =================

PRICE_TEXT = """💎 Diamond ဈေးနှုန်းများ

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
    55: 4850, 86: 5350, 165: 14350, 172: 15050,
    257: 22350, 275: 23850, 343: 30050,
    565: 48850, 706: 61050, 2195: 189050,
    3688: 317350, 5532: 475950, 9288: 799050
}

PASS_PRICES = {
    "weekly1": 6550,
    "weekly2": 13100,
    "weekly3": 19650,
    "twilight": 35050
}

user_data = {}

def get_user(uid):
    if uid not in user_data:
        user_data[uid] = {"state": STATE_IDLE}
    return user_data[uid]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if not shop_open():
        await update.message.reply_text("🔒 ဆိုင်ပိတ်ထားပါတယ်။\n🕒 ဆိုင်ဖွင့်ချိန်ကတော့ (11:00 - 19:30) ဖြစ်ပါတယ်နော်။")
        return

    uid = update.effective_chat.id
    user_data[uid] = {"state": STATE_GET_ID}

    await update.message.reply_text(
        "👋 မင်္ဂလာပါ!\n🎮 Pepe's Diamond Shop မှ ကြိုဆိုပါတယ်နော်။\n\n"
        "📌 Diamond ထည့်ပေးရမယ့် Game ID ပို့ပေးပါ။\n👉 ဥပမာ - Pepe 1600113465 (16740)"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_chat.id
    data = get_user(uid)
    current_state = data.get("state", STATE_IDLE)

    # 1. ID လက်ခံခြင်း အဆင့်
    if current_state == STATE_GET_ID:
        if not update.message.text:
            return
        data["id"] = update.message.text
        data["state"] = STATE_GET_SERVER

        keyboard = [
            [InlineKeyboardButton("🇲🇲 Myanmar", callback_data=f"mm_{uid}")],
            [InlineKeyboardButton("🇸🇬 Singapore", callback_data=f"sg_{uid}")],
            [InlineKeyboardButton("🚫 Ban", callback_data=f"ban_{uid}")]
        ]

        await context.bot.send_message(
            ADMIN_ID,
            f"🔍 ID အသစ် စစ်ဆေးရန်\n{update.message.text}\nUSER ID: {uid}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await update.message.reply_text("⏳ Admin ဘက်က ID စစ်ပေးနေလို့ ခေတ္တစောင့်ဆိုင်းပေးပါနော်...")
        return

    # 2. ပမာဏ လက်ခံခြင်း အဆင့် (STATE_GET_AMOUNT)
    elif current_state == STATE_GET_AMOUNT:
        if not update.message.text:
            return
        text = update.message.text.lower().strip().replace(" ", "")

        if "server" not in data:
            await update.message.reply_text("❌ စနစ်ပိုင်းဆိုင်ရာ မှားယွင်းမှုရှိသွားလို့ /start ကို ပြန်နှိပ်ပေးပါ။")
            data["state"] = STATE_IDLE
            return

        # Pass အမျိုးအစားများကို သတ်မှတ်ချက်အတိုင်း စစ်ဆေးခြင်း
        if text in ["wp1", "weeklypass1", "weekly1", "wp 1", "wp_1"]:
            value = "weekly1"
        elif text in ["wp2", "weeklypass2", "weekly2", "wp 2", "wp_2"]:
            value = "weekly2"
        elif text in ["wp3", "weeklypass3", "weekly3", "wp 3", "wp_3"]:
            value = "weekly3"
        elif text in ["twi", "twilight", "twilightpass"]:
            value = "twilight"
        else:
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
            await update.message.reply_text("❌ ဝယ်ယူလိုတဲ့ ပမာဏ သို့မဟုတ် အမျိုးအစား မှားယွင်းနေလို့ သေချာပြန်ရိုက်ပေးပါနော်။")
            return

        if data["server"] == "sg":
            price += SG_EXTRA

        display_item = value
        if value == "weekly1":
            display_item = "Weekly Pass 1"
        elif value == "weekly2":
            display_item = "Weekly Pass 2"
        elif value == "weekly3":
            display_item = "Weekly Pass 3"
        elif value == "twilight":
            display_item = "Twilight Pass"
        else:
            display_item = f"{value} Diamond"

        data["amount"] = value
        data["price"] = price
        data["state"] = STATE_CONFIRM

        await update.message.reply_text(
            f"🔍 အော်ဒါအချက်အလက်ကို ပြန်စစ်ပေးပါ။\n\n"
            f"• ဝယ်ယူမည့်အမျိုးအစား: {display_item}\n"
            f"• ကျသင့်ငွေ: {price:,} MMK\n\n"
            f"👉 အတည်ပြုပြီး ဝယ်ယူမယ်ဆိုရင် YES ဟု စာလုံးကြီးဖြင့် ရိုက်ပို့ပေးပါနော်။"
        )
        return

    # 3. အော်ဒါ အတည်ပြုခြင်း အဆင့် (STATE_CONFIRM)
    elif current_state == STATE_CONFIRM:
        if not update.message.text:
            return
        
        if update.message.text.upper() != "YES":
            data["state"] = STATE_GET_AMOUNT
            await update.message.reply_text(
                "❌ အော်ဒါကို အတည်မပြုခဲ့ပါဘူး။\n"
                "ဝယ်ယူလိုတဲ့ Diamond ပမာဏ သို့မဟုတ် အမျိုးအစားကို ပြန်လည်ရိုက်ထည့်ပေးပါနော်။\n\n"
                "💡 [သတိပြုရန်]\n"
                "Weekly Pass အတွက် wp 1, wp 2, wp 3 ဟု ရိုက်ပေးပါ။\n"
                "Twilight Pass အတွက် twi ဟု ရိုက်ပေးပါ။"
            )
            return

        data["state"] = STATE_WAIT_PAYMENT
        await update.message.reply_text(
            f"💳 ငွေပေးချေရမယ့် အကောင့်အချက်အလက်များ\n\n"
            f"• KBZPay: {KBZPAY}\n"
            f"• WavePay: {WAVEPAY}\n\n"
            f"📸 ငွေလွှဲပြီးသွားရင် ဖြတ်ပိုင်း (Screenshot) လေးကို ဒီမှာ ပို့ပေးခဲ့ပါနော်။"
        )
        return

    # 4. ငွေလွှဲစောင့်ဆိုင်းခြင်း အဆင့် (STATE_WAIT_PAYMENT)
    elif current_state == STATE_WAIT_PAYMENT:
        if not update.message.photo:
            await update.message.reply_text("❌ ငွေလွှဲဖြတ်ပိုင်း Screenshot ပုံ ပို့ပေးရပါမယ်။ ပုံလေးပြန်ပို့ပေးပါ။")
            return

        keyboard = [
            [InlineKeyboardButton("✅ ACCEPT", callback_data=f"acc_{uid}")],
            [InlineKeyboardButton("❌ REJECT", callback_data=f"rej_{uid}")]
        ]

        await context.bot.send_message(
            ADMIN_ID,
            f"💰 ငွေလွှဲဖြတ်ပိုင်းအသစ် ရောက်ရှိလာပါပြီ\nUSER ID: {uid}\nID: {data.get('id')}\nပမာဏ: {data.get('amount')}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        await context.bot.forward_message(ADMIN_ID, uid, update.message.message_id)
        await update.message.reply_text("✨ ငွေလွှဲဖြတ်ပိုင်း လက်ခံရရှိပါပြီ။\nAdmin က စစ်ဆေးပြီးတာနဲ့ Diamond ချက်ချင်းထည့်သွင်းပေးသွားမှာမို့ ခေတ္တစောင့်ပေးပါနော်။")
        
        data["state"] = STATE_IDLE
        return


# ================= SERVER CALLBACK (ADMIN ACTION) =================

async def server_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    data = get_user(uid)

    if action == "ban":
        await context.bot.send_message(uid, "❌ စည်းကမ်းချက်များနှင့် မကိုက်ညီလို့ အော်ဒါကို ငြင်းပယ်ထားပါတယ်။")
        data["state"] = STATE_IDLE
        return

    data["server"] = action
    data["state"] = STATE_GET_AMOUNT

    await context.bot.send_message(
        uid,
        f"🎯 ရွေးချယ်ထားသော Server: {action.upper()}\n\n"
        f"{PRICE_TEXT}\n"
        f"👉 ဝယ်ယူလိုသည့် ပမာဏကို ရိုက်ထည့်ပေးပါ။\n\n"
        f"💡 [သတိပြုရန်]\n"
        f"Weekly Pass ဝယ်ယူလိုပါက wp 1, wp 2, wp 3 ဟု ရိုက်ထည့်ပေးပါ။\n"
        f"Twilight Pass ဝယ်ယူလိုပါက twi ဟု ရိုက်ထည့်ပေးပါ။"
    )


# ================= ADMIN ACTIONS CALLBACK =================

async def admin_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, uid = query.data.split("_")
    uid = int(uid)

    if action == "rej":
        await context.bot.send_message(uid, "❌ ပေးပို့ထားတဲ့ ငွေလွှဲဖြတ်ပိုင်း အဆင်မပြေလို့ အော်ဒါကို ငြင်းပယ်ထားပါတယ်။ အချက်အလက်များ ပြန်လည်စစ်ဆေးပေးပါ။")
        return

    await context.bot.send_message(uid, "⏳ ငွေလွှဲပြေစာ စစ်ဆေးပြီးပါပြီ။ Diamond များ ထည့်သွင်းပေးနေပြီမို့ ခေတ္တစောင့်ဆိုင်းပေးပါနော်...")

    await context.bot.send_message(
        ADMIN_ID,
        f"User {uid} အော်ဒါကို လက်ခံလိုက်ပါပြီ။",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏁 FINISH", callback_data=f"fin_{uid}")]
        ])
    )


# ================= FINISH CALLBACK =================

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, uid = query.data.split("_")
    uid = int(uid)

    await context.bot.send_message(uid, "🎉 အကောင့်ထဲကို Diamond များ ထည့်သွင်းမှု အောင်မြင်စွာ ပြီးဆုံးပါပြီ!\nPepe's Diamond Shop ကို အားပေးတဲ့အတွက် အထူးပင် ကျေးဇူးတင်ရှိပါတယ်နော်။ 🥰")


# ================= MAIN =================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(server_buttons, pattern="^(mm|sg|ban)_"))
    app.add_handler(CallbackQueryHandler(admin_actions, pattern="^(acc|rej)_"))
    app.add_handler(CallbackQueryHandler(finish, pattern="^fin_"))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))

    print("BOT RUNNING 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
