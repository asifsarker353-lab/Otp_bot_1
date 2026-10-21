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
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8702093778:AAEA9hvLZbXY89mJNQUm_S5L4uxj_odXi4M")
BOT_USERNAME = "VoidPlusOtpBot"
ADMIN_ID = 7914231611
OTP_GROUP_ID = -1004451897474
OTP_GROUP_LINK e.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Aapnar file upload korar permission nei!")
        return

    document = update.message.document
    
    try:
        file = await context.bot.get_file(document.file_id)
        temp_path = "temp_up.txt"
        await file.download_to_drive(temp_path)

        with open(temp_path, "r", encoding="utf-8") as f_in:
            new_lines = [line.strip() for line in f_in if line.strip() and not line.startswith("#")]

        mode = admin_states.get(user_id)
        
        if mode == "replace_file":
            with open("master_numbers.txt", "w", encoding="utf-8") as f_out:
                for line in new_lines:
                    f_out.write(f"{line}\n")
            admin_states[user_id] = None
            await update.message.reply_text(
                f"✅ **Old File Cleared & New Numbers Saved!**\n🔢 Total New Numbers: `{len(new_lines)}`", 
                parse_mode="Markdown"
            )
        else:
            with open("master_numbers.txt", "a", encoding="utf-8") as f_out:
                for line in new_lines:
                    f_out.write(f"\n{line}")
            await update.message.reply_text(
                f"✅ **New Numbers Appended!**\n🔢 Total New Lines: `{len(new_lines)}`", 
                parse_mode="Markdown"
            )

        if os.path.exists(temp_path):
            os.remove(temp_path)

    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    state = admin_states.get(user_id)
    text = update.message.text.strip()

    if state == "awaiting_country_add":
        # Format: Name, Code, Flag, Dialing (e.g. India, IN, 🇮🇳, 91)
        try:
            parts = [p.strip() for p in text.split(",")]
            if len(parts) == 4:
                c_name, c_code, c_flag, c_dialing = parts
                full_name = f"{c_flag} {c_name}"
                COUNTRIES.append((full_name, c_code.upper(), c_flag, c_dialing))
                COUNTRY_DICT[c_code.upper()] = (c_flag, c_dialing)
                admin_states[user_id] = None
                await update.message.reply_text(f"✅ Notun country added: {full_name} ({c_code.upper()})")
            else:
                await update.message.reply_text("❌ Format vul hoyeche! Chesta korun: `Name, Code, Flag, Dialing` (যেমন: India, IN, 🇮🇳, 91)", parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {e}")

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = update.effective_user.id

    try:
        await query.answer()
    except Exception:
        pass

    if query.data.startswith("copycode_"):
        return

    # Admin Callback Handling
    if user_id == ADMIN_ID:
        if query.data == "admin_stats":
            total, stats = get_all_file_numbers_count()
            msg = f"📊 **Number Statistics**\n\n🔢 **Total Numbers in File:** `{total}`\n\n"
            for code, count in stats.items():
                flag = COUNTRY_DICT.get(code, ("🏳️", ""))[0] if code in COUNTRY_DICT else "🌐"
                msg += f"{flag} `{code}`: {count} numbers\n"
            await query.edit_message_text(text=msg, parse_mode="Markdown", reply_markup=get_admin_keyboard())
            return

        elif query.data == "admin_clear_all":
            admin_states[user_id] = "replace_file"
            await query.edit_message_text(
                text="⚠️ **Replace Mode Active!**\n\n"
                     "Ekhon kono .txt file pathale purono Shob number Moche jabe ebong notun file-er number add hobe.\n\n"
                     "📌 *File pathan ki na cancel korte niche click korun.*",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="admin_cancel")]])
            )
            return

        elif query.data == "admin_add_country":
            admin_states[user_id] = "awaiting_country_add"
            await query.edit_message_text(
                text="➕ **Add New Country**\n\n"
                     "Nicher format e country-er details likhe text message pathan:\n"
                     "`CountryName, Code, Flag, DialingCode`\n\n"
                     "Example: `India, IN, 🇮🇳, 91`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Cancel", callback_data="admin_cancel")]])
            )
            return

        elif query.data == "admin_remove_country":
            keyboard = []
            for name, code, _, _ in COUNTRIES:
                keyboard.append([InlineKeyboardButton(f"❌ Remove {name}", callback_data=f"rem_c_{code}")])
            keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
            await query.edit_message_text(text="🗑️ Select country to remove:", reply_markup=InlineKeyboardMarkup(keyboard))
            return

        elif query.data.startswith("rem_c_"):
            rem_code = query.data.replace("rem_c_", "")
            global COUNTRIES
            COUNTRIES = [c for c in COUNTRIES if c[1] != rem_code]
            if rem_code in COUNTRY_DICT:
                del COUNTRY_DICT[rem_code]
            await query.edit_message_text(text=f"✅ Country `{rem_code}` Removed!", parse_mode="Markdown", reply_markup=get_admin_keyboard())
            return

        elif query.data == "admin_cancel" or query.data == "admin_back":
            admin_states[user_id] = None
            await query.edit_message_text(text="⚙️ **Admin Control Panel**", reply_markup=get_admin_keyboard(), parse_mode="Markdown")
            return

    # User Standard Callback Handling
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
            await query.edit_message_text(text=text_content, parse_mode="Markdown", reply_markup=kb)
        except Exception:
            pass

        primary = fetched_numbers[0]
        if primary:
            asyncio.create_task(check_otp_loop(query, country_code, primary, context, user_id))

    elif query.data == "change_country":
        try:
            await query.edit_message_text(
                "✨ **Dust Bot High-Speed System** ✨\n\n👇 *Select a country below:*", 
                reply_markup=get_country_keyboard(),
                parse_mode="Markdown"
            )
        except Exception:
            pass

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Start the bot & select country"),
        BotCommand("admin", "Admin Control Panel")
    ]
    try:
        await application.bot.set_my_commands(commands)
    except Exception:
        pass

def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).read_timeout(10).connect_timeout(10).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.add_handler(CallbackQueryHandler(button_click))

    try:
        app.job_queue.run_once(lambda ctx: asyncio.create_task(set_bot_commands(app)), 1)
    except Exception:
        pass

    print("Master-File Ultra-Fast Bot with Admin Panel is running...")
    app.run_polling()

if __name__ == "__main__":
    main(){})
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
