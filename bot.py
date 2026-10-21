import logging
import requests
import asyncio
import os
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters, ContextTypes
)

# Configuration
TELEGRAM_BOT_TOKEN = "8702093778:AAEA9hvLZbXY89mJNQUm_S5L4uxj_odXi4M"
BOT_USERNAME = "VoidPlusOtpBot"
ADMIN_ID = 7914231611
OTP_GROUP_ID = -1004451897474
OTP_GROUP_LINK = "https://t.me/void_otp_group"

API_KEY = "np_live_V_y4jdSBzOlgVxNAlZQIkh-jUtOI_MHz_v-gh17N7j8"
BASE_URL = "https://numberpanel.tech"

logging.basicConfig(level=logging.INFO)

user_last_message = {}
user_sessions = {}

# কান্ট্রি, কোড, ফ্ল্যাগ ও ডায়ালিং কোড ম্যাপিং
COUNTRIES = [
    ("🇹🇿 Tanzania", "TZ", "🇹🇿", "255"),
    ("🇸🇩 Sudan", "SD", "🇸🇩", "249"),
    ("🇾🇪 Yemen", "YE", "🇾🇪", "967"),
    ("🇸🇳 Senegal", "SN", "🇸🇳", "221"),
    ("🇵🇪 Peru", "PE", "🇵🇪", "51")
]

COUNTRY_DICT = {code: (flag, dialing) for _, code, flag, dialing in COUNTRIES}

HEADERS = {
    "Authorization": f"Bearer {API_KEY.strip()}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# 📁 সেন্ট্রাল ফাইল থেকে নির্দিষ্ট দেশের নম্বর ফিল্টার করে নেওয়ার ফাংশন
def get_numbers_for_country(country_code, dialing_code, count=3):
    master_file = "master_numbers.txt"
    country_numbers = []
    
    if os.path.exists(master_file):
        with open(master_file, "r", encoding="utf-8") as f:
            for line in f:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#"):
                    if clean_line.replace("+", "").startswith(dialing_code):
                        country_numbers.append(clean_line if clean_line.startswith("+") else "+" + clean_line)

    if len(country_numbers) < count:
        for _ in range(count - len(country_numbers)):
            rand_num = f"+{dialing_code}" + "".join([str(random.randint(0, 9)) for _ in range(9)])
            if rand_num not in country_numbers:
                country_numbers.append(rand_num)

    return random.sample(country_numbers, min(count, len(country_numbers)))

def check_otp(phone_number):
    try:
        response = requests.get(f"{BASE_URL}/api/my_numbers", headers=HEADERS, timeout=3)
        if response.status_code == 200:
            data = response.json()
            numbers = []
            if isinstance(data, list):
                numbers = data
            elif isinstance(data, dict):
                numbers = data.get("numbers", []) or data.get("data", []) or data.get("items", [])
            
            target = phone_number.replace("+", "").strip()

            for num in numbers:
                num_phone = str(num.get("number") or num.get("phone") or num.get("full_number") or "").replace("+", "").strip()

                if target in num_phone or num_phone in target:
                    sms = (
                        num.get("sms") or 
                        num.get("code") or 
                        num.get("otp") or 
                        num.get("latest_sms") or 
                        num.get("message") or 
                        num.get("text")
                    )
                    
                    if not sms and isinstance(num, dict):
                        for k, v in num.items():
                            if any(w in k.lower() for w in ["sms", "code", "otp", "text", "msg"]) and v:
                                sms = v
                                break

                    if sms:
                        return str(sms)
        return None
    except Exception as e:
        print(f"OTP Check Error: {e}")
        return None

def get_country_keyboard():
    keyboard = []
    for i in range(0, len(COUNTRIES), 2):
        row = [InlineKeyboardButton(COUNTRIES[i][0], callback_data=f"country_{COUNTRIES[i][1]}")]
        if i + 1 < len(COUNTRIES):
            row.append(InlineKeyboardButton(COUNTRIES[i+1][0], callback_data=f"country_{COUNTRIES[i+1][1]}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🪐 OTP Group ↗️", url=OTP_GROUP_LINK)])
    return InlineKeyboardMarkup(keyboard)

def format_number_display(phone, dialing_code, remove_cc):
    clean_phone = phone.replace("+", "")
    if remove_cc and clean_phone.startswith(dialing_code):
        return clean_phone[len(dialing_code):]
    return phone if phone.startswith("+") else f"+{phone}"

def generate_number_layout(country_code, numbers, hide_cc=False):
    flag, dialing = COUNTRY_DICT.get(country_code, ("🏳️", ""))
    
    text_lines = [
        f"{flag} **{country_code} Allocated** 💬 **WhatsApp**",
        f"👵 **Waiting for OTP......** 🔽\n"
    ]
    
    for num in numbers:
        if num:
            disp_num = format_number_display(num, dialing, hide_cc)
            text_lines.append(f"{flag} 📋 `{disp_num}`")
        else:
            text_lines.append(f"{flag} ❌ Unavailable")

    text_body = "\n".join(text_lines)

    keyboard = [
        [InlineKeyboardButton("🪐 OTP Group ↗️", url=OTP_GROUP_LINK)]
    ]
    
    toggle_text = "✅ Add Country Code" if hide_cc else "❌ Remove Country Code"
    keyboard.append([InlineKeyboardButton(toggle_text, callback_data=f"togglecc_{country_code}")])
    
    keyboard.append([
        InlineKeyboardButton("🔗 Country", callback_data="change_country"),
        InlineKeyboardButton("🔄 Change", callback_data=f"chgnum_{country_code}")
    ])
    
    return text_body, InlineKeyboardMarkup(keyboard)

async def check_otp_loop(query, country_code, primary_phone, context, user_id):
    flag, dialing = COUNTRY_DICT.get(country_code, ("🏳️", ""))
    
    for step in range(30):
        await asyncio.sleep(3)
        otp = check_otp(primary_phone)
        
        if otp:
            otp_keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(f"💬 📋 `{otp}`", callback_data=f"copycode_{otp}")]
            ])

            try:
                session = user_sessions.get(user_id, {})
                hide_cc = session.get("hide_cc", False)
                disp_primary = format_number_display(primary_phone, dialing, hide_cc)
                
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"{flag} 💬 `{disp_primary}`\n\nOTP Code: `{otp}`",
                    parse_mode="Markdown",
                    reply_markup=otp_keyboard
                )
            except Exception:
                pass

            try:
                group_kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 WhatsApp", callback_data=f"copycode_{otp}")],
                    [
                        InlineKeyboardButton("📡 Channel ↗️", url=OTP_GROUP_LINK),
                        InlineKeyboardButton("🚀 Number ↗️", url=f"https://t.me/{BOT_USERNAME}")
                    ]
                ])

                clean_otp = str(otp).strip()
                group_text = (
                    f"{flag} **#{country_code}** 💬 **{primary_phone}** |\n"
                    f"🔊 **English**\n\n"
                    f"```\n"
                    f"Votre compte WhatsApp sera enregistré sur un nouvel appareil.\n"
                    f"Votre code WhatsApp : {clean_otp}\n"
                    f"```"
                )

                await context.bot.send_message(
                    chat_id=OTP_GROUP_ID, 
                    text=group_text, 
                    parse_mode="Markdown",
                    reply_markup=group_kb
                )
            except Exception as e:
                print(f"Group Forward Error: {e}")
            
            return

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    
    try:
        await update.message.delete()
    except Exception:
        pass

    if user_id in user_last_message:
        try:
            await context.bot.delete_message(chat_id=user_id, message_id=user_last_message[user_id])
        except Exception:
            pass

    reply_markup = get_country_keyboard()
    sent_message = await update.message.reply_text(
        "✨ **Dust Bot High-Speed System** ✨\n\n"
        "🟢 *Virtual numbers are online & ready.*\n"
        "👇 *Select a country below to start:*", 
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    user_last_message[user_id] = sent_message.message_id

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনার ফাইল আপলোড করার অনুমতি নেই!")
        return

    document = update.message.document
    
    try:
        file = await context.bot.get_file(document.file_id)
        temp_path = "temp_up.txt"
        await file.download_to_drive(temp_path)

        with open(temp_path, "r", encoding="utf-8") as f_in:
            new_lines = [line.strip() for line in f_in if line.strip() and not line.startswith("#")]

        with open("master_numbers.txt", "a", encoding="utf-8") as f_out:
            for line in new_lines:
                f_out.write(f"\n{line}")

        os.remove(temp_path)
        await update.message.reply_text(
            f"✅ ফাইল সফলভাবে যুক্ত হয়েছে!\n🔢 মোট নতুন লাইন: `{len(new_lines)}`", 
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ ত্রুটি হয়েছে: {e}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id

    try:
        await query.answer()
    except Exception:
        pass

    if query.data.startswith("copycode_"):
        return

    user_last_message[user_id] = query.message.message_id

    if query.data.startswith("togglecc_"):
        country_code = query.data.split("_", 1)[1]
        session = user_sessions.get(user_id, {})
        current_state = session.get("hide_cc", False)
        session["hide_cc"] = not current_state
        user_sessions[user_id] = session
        
        numbers = session.get("numbers", [])
        text_content, kb = generate_number_layout(country_code, numbers, session["hide_cc"])
        
        try:
            await query.edit_message_text(text=text_content, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass
        return

    if query.data.startswith("country_") or query.data.startswith("chgnum_"):
        country_code = query.data.split("_", 1)[1]
        _, dialing = COUNTRY_DICT.get(country_code, ("🏳️", ""))
        
        fetched_numbers = get_numbers_for_country(country_code, dialing, 3)

        user_sessions[user_id] = {
            "country": country_code,
            "numbers": fetched_numbers,
            "hide_cc": False
        }

        text_content, kb = generate_number_layout(country_code, fetched_numbers, False)

        try:
            await query.edit_message_text(
                text=text_content,
                parse_mode="Markdown",
                reply_markup=kb
            )
        except Exception:
            pass

        primary = fetched_numbers[0]
        if primary:
            asyncio.create_task(check_otp_loop(query, country_code, primary, context, user_id))

    elif query.data == "change_country":
        try:
            await query.edit_message_text(
                "✨ **Dust Bot High-Speed System** ✨\n\n"
                "👇 *Select a country below:*", 
                reply_markup=get_country_keyboard(),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    elif query.data == "none":
        pass

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Start the bot & select country")
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception:
        pass

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(10).connect_timeout(10).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(CallbackQueryHandler(button_click))

    try:
        app.job_queue.run_once(lambda ctx: asyncio.create_task(set_bot_commands(app)), 1)
    except Exception:
        pass

    print("Master-File Ultra-Fast Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
