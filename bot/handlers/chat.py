import re
import os
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import StorageKey
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_i18n.context import I18nContext
from dotenv import load_dotenv

load_dotenv()

from states.chat import SupportState

router = Router()
ADMIN_ID = int(os.getenv("SUPER_ADMIN"))


@router.message(Command("help"))
async def help_handler(msg: types.Message, state: FSMContext, i18n: I18nContext):
    """User yordam so'raganda chatni ochish"""
    await state.set_state(SupportState.on_chat)
    await msg.answer(i18n.get("support_started")) 
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(
        text="Chatni yopish ❌", 
        callback_data=f"close_chat_{msg.from_user.id}")
    )
    
    await msg.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"🆘 <b>Yangi yordam so'rovi!</b>\n"
             f"👤 Kimdan: {msg.from_user.full_name}\n"
             f"🆔 ID: <code>{msg.from_user.id}</code>\n\n"
             f"<i>Javob berish uchun 'Reply' qiling yoki tugmani bosing.</i>",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.message(SupportState.on_chat)
async def user_to_admin(msg: types.Message, bot: Bot):
    """User yozgan xabarni adminga nusxalash"""
    if msg.text:
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(
            text="Chatni yopish ❌", 
            callback_data=f"close_chat_{msg.from_user.id}")
        )
        
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📩 <b>Xabar keldi (ID: <code>{msg.from_user.id}</code>):</b>\n\n{msg.text}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

# --- ADMIN QISMI ---

@router.callback_query(F.data.startswith("close_chat_"))
async def admin_close_chat_callback(callback: types.CallbackQuery, bot: Bot):
    """Tugma bosilganda chatni yopish"""
    user_id = int(callback.data.split("_")[2])
    
    from main import dp 
    
    user_storage_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
    
    await dp.storage.set_state(key=user_storage_key, state=None)
    await dp.storage.set_data(key=user_storage_key, data={})
    
    try:
        await bot.send_message(user_id, "❌ Admin chatni yakunladi. Asosiy menyuga qaytdingiz.")
    except:
        pass 

    await callback.message.edit_text(f"{callback.message.text}\n\n✅ <b>Chat yopildi!</b>", parse_mode="HTML")
    await callback.answer("Chat yopildi!")

@router.message(F.reply_to_message, F.chat.id == ADMIN_ID)
async def admin_reply_to_user(msg: types.Message, bot: Bot):
    """Admin 'Reply' orqali javob yozganda"""
    reply_text = msg.reply_to_message.text or msg.reply_to_message.caption
    match = re.search(r"ID: (\d+)", reply_text)
    
    if match:
        user_id = int(match.group(1))
        
        if msg.text.strip() == "/close":
            from main import dp
            user_storage_key = StorageKey(bot_id=bot.id, chat_id=user_id, user_id=user_id)
            await dp.storage.set_state(key=user_storage_key, state=None)
            await bot.send_message(user_id, "❌ Admin chatni yakunladi.")
            await msg.answer(f"✅ User {user_id} bilan chat yopildi.")
        else:
            try:
                await bot.send_message(user_id, f"👨‍💻 <b>Admin javobi:</b>\n\n{msg.text}", parse_mode="HTML")
                await msg.answer("✅ Xabar yuborildi.")
            except Exception:
                await msg.answer(f"❌ Foydalanuvchi botni bloklagan.")
    else:
        await msg.answer("⚠️ User ID topilmadi. ID bor xabarga reply qiling.")