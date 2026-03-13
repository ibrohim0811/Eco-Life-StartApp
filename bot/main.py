import os
import sys
import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()


import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Bot
from aiogram.filters import Command
from pathlib import Path
from aiogram import types
from aiogram.types import ReactionTypeEmoji
from aiogram_i18n import I18nContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext


from accounts.models import Users
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from middleware.i18n import i18n_middleware
from aiogram_i18n.context import I18nContext
from handlers.register import register
from handlers.account import acc
from handlers.faq import faq 
from handlers.forgot_password import dp as forgot_password
from admin.admin import dp_admin
from handlers.alert import dp as alert
from handlers.chat import router 
from handlers.payment import payment
from UI.default import sorov, main_menu
from UI.inline import settings_lang, change_lang
from bot.connections import get_user, get_user_language
from accounts.models import Subscription

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env") 
env_path = BASE_DIR / ".env"
dp = Dispatcher(storage=MemoryStorage())
i18n_middleware.setup(dispatcher=dp)
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

def get_and_check_sub(user):
    
    sub, created = Subscription.objects.get_or_create(user=user)
    sub.check_subscription_status()
    return sub

@dp.message(Command('start'))
async def start(msg: types.Message, i18n: I18nContext):
    user = await sync_to_async(get_user)(msg.from_user.id)
    await sync_to_async(get_and_check_sub)(user)
    user_language = await sync_to_async(get_user_language)(tg_id=msg.from_user.id)
    if user:
        if user.is_banned:
            await i18n.set_locale(msg.from_user.language_code)
            await msg.answer(i18n("banned"), reply_markup=types.ReplyKeyboardRemove())
            return 
        
        else:
            await i18n.set_locale(user_language)
            await msg.answer(
                f"👋{i18n('hello')} {msg.from_user.first_name} {i18n('start_text')}", 
                reply_markup=main_menu(i18n)
            )
    
    else:
        await i18n.set_locale(msg.from_user.language_code)
        await msg.answer(
            f"👋{i18n('hello')} {msg.from_user.first_name} {i18n('start_text')}", 
            reply_markup=sorov(i18n)
        )
        


@dp.message(F.text == '⬅️')
async def back_to_main(msg: types.Message, state: FSMContext, i18n: I18nContext):
    await msg.answer('⬅️', reply_markup=main_menu(i18n))
    await state.clear()    
 
        

THANKS_WORDS = [
    "rahmat", "raxmat", "tashakkur", 
    "спасибо", "благодарю", 
    "thanks", "thank you", "thx"
]

@dp.message(F.text, lambda msg: any(word in msg.text.lower() for word in THANKS_WORDS))
async def handle_thanks_reaction(message: types.Message):
    try:
        await bot.set_message_reaction(
            chat_id=message.chat.id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji="❤️‍🔥")],
            is_big=True
        )
    except Exception as e:
        print(f"Xato: {e}")
    




    
async def set_user_language(user_id: int, lang_code: str):
    def update_db():
        return Users.objects.filter(tg_id=user_id).update(language=lang_code)
    await sync_to_async(update_db)()

# 2. Tilni tanlash komandasi
@dp.message(Command('change_lang'))
async def change_lang(msg: types.Message, i18n: I18nContext):
    user = await sync_to_async(get_user)(tg_id=msg.from_user.id)
    if user:
        await msg.answer(
        text=i18n("select_lang"), 
        reply_markup=change_lang(i18n)
    )
    else:
        await msg.answer(i18n("register_required"))


@dp.callback_query(F.data.in_({"uzbek", "rus", "en"}))
async def language_handler(callback: types.CallbackQuery, i18n: I18nContext):
    new_lang = callback.data
    
    await set_user_language(callback.from_user.id, new_lang)
    
    await i18n.set_locale(new_lang)
    
    await callback.message.edit_text(
        text=i18n("sucsess_lang"),
        reply_markup=None 
    )
    
    await callback.message.answer(
        text=i18n("start_text"), 
        reply_markup=main_menu(i18n)
    )
    
    await callback.answer()
    
    
    
    



async def main():
    bot = Bot(token=BOT_TOKEN)
    dp.update.middleware(i18n_middleware)
    dp.include_router(register)
    dp.include_router(acc)
    dp.include_router(faq)
    dp.include_router(forgot_password)
    dp.include_router(alert)
    dp.include_router(dp_admin)
    dp.include_router(router)
    dp.include_router(payment)
    await dp.start_polling(bot)


if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)

    asyncio.run(main()) 
        