import sys
import os
import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()


from aiogram import Router, types, F
from asgiref.sync import sync_to_async
from middleware.i18n import i18n_middleware
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from aiogram_i18n.context import I18nContext
from django.contrib.auth.hashers import make_password


from states.register import Register
from UI.inline import settings_lang
from UI.default import contact_button, main_menu
from accounts.models import Users



dp = Router()

def get_user_info(tg_id):
    return Users.objects.filter(tg_id=tg_id).first()

@dp.message(lambda message, i18n: message.text == i18n("register"))
async def register(msg: types.Message, state: FSMContext, i18n: I18nContext):
    
    await state.set_state(Register.set_lang)
    lang =  msg.from_user.language_code
    await i18n.set_locale(lang)
    await msg.answer(i18n("select_lang"), reply_markup=settings_lang(i18n))
    
    
    
@dp.callback_query(Register.set_lang, F.data.in_(["uzbek", "rus", "en"]))
async def set_language(callback: types.CallbackQuery, state: FSMContext, i18n: I18nContext):
    lang_map = {"uzbek": "uz", "rus": "ru", "en": "en"}
    selected_lang = lang_map[callback.data]
    
    await i18n.set_locale(selected_lang)
    
    await state.update_data(user_lang=selected_lang)
    
    await state.set_state(Register.first_name)
    
    await callback.answer(i18n.get("sucsess_lang"))
    await callback.message.edit_text(i18n.get("name"))


@dp.message(Register.first_name)
async def first_name_get(msg: types.Message, state: FSMContext, i18n: I18nContext):
    if any(c.isdigit() for c in msg.text):
        await msg.answer(i18n.get("invalid_name"))
        await msg.answer(i18n.get("name"))
        await state.set_state(Register.first_name)
        return 

    await state.update_data(first_name=msg.text)
    
    await state.set_state(Register.last_name)
    await msg.answer(i18n("last_name"))
    
    
@dp.message(Register.last_name)
async def last_name_get(msg: types.Message, state: FSMContext, i18n: I18nContext):
    if any(c.isdigit() for c in msg.text):
        
        await msg.answer(i18n.get("invalid_last_name"))
        await msg.answer(i18n.get("last_name"))
        await state.set_state(Register.last_name)
        return

    await state.update_data(last_name=msg.text)
    
    await state.set_state(Register.phone)
    await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))
    
    
    
from validation.validate import validate_phone_number
@dp.message(Register.phone)
async def phone_get(msg: types.Message, state: FSMContext, i18n: I18nContext):
    if msg.contact:
        phone = msg.contact.phone_number

        if validate_phone_number(phone):
            await state.update_data(phone=phone)
            await state.set_state(Register.password)
            await msg.answer(i18n("password"))
            return
        else:
            await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))
            return

    if msg.text:
        phone = msg.text

        if validate_phone_number(phone):
            await state.update_data(phone=phone)
            await state.set_state(Register.password)
            await msg.answer(i18n("password"))
            return

    await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))
    
    
    
@dp.message(Register.password)
async def password(msg: types.Message, state: FSMContext, i18n: I18nContext):
    password = msg.text
    
    await state.update_data(password=password)
    data = await state.get_data()
    user = await sync_to_async(Users.objects.create)(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        phone=data.get("phone"),
        username=msg.from_user.username or f"user_{msg.from_user.id}",
        password=make_password(data.get("password")),
        tg_id=msg.from_user.id,
        language=data.get('user_lang')
    )
    
    await msg.answer(f"{i18n('start_text')} \n {i18n('web')} \n Username: {user.username} \n {i18n('parol')}: <tg-spoiler>{data.get('password')}</tg-spoiler> \n {msg.from_user.first_name} \n{i18n('join')}\n https://Eco-life.uz", parse_mode="HTML", reply_markup=main_menu(i18n))
    await state.clear()

    
    
    
#language_settings
@dp.callback_query(lambda c: c.data == "uzbek")
async def uzbek(callback: types.CallbackQuery, i18n: I18nContext):
    await i18n.set_locale("uz")
    await callback.message.answer(i18n("sucsess_lang"))
    await callback.answer()
    
#rus 
@dp.callback_query(lambda c: c.data == "rus")
async def rus(callback: types.CallbackQuery, i18n: I18nContext):
    await i18n.set_locale("ru")
    await callback.message.answer(i18n("sucsess_lang"))
    await callback.answer()

#ingliz 
@dp.callback_query(lambda c: c.data == "en")
async def english(callback: types.CallbackQuery, i18n: I18nContext):
    await i18n.set_locale("en")
    await callback.message.answer(i18n("sucsess_lang"))
    
    
