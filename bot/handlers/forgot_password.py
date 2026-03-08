import sys
import os
import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from states.forgot import ForgotPassword
from asgiref.sync import sync_to_async
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from accounts.models import Users
from aiogram_i18n.context import I18nContext
from UI.default import contact_button
from validation.validate import validate_phone_number

dp = Router()

@sync_to_async
def get_user_by_tg_id(tg_id):
    return Users.objects.filter(tg_id=tg_id).first()

@sync_to_async
def update_user_password(tg_id, new_password):
    return Users.objects.filter(tg_id=tg_id).update(password=new_password)



@dp.message(lambda message, i18n: message.text == i18n('forgot_password'))
async def forgot_password_start(msg: types.Message, i18n: I18nContext, state: FSMContext):
    user = await get_user_by_tg_id(msg.from_user.id)
    if not user:
        await msg.answer("Ro'yxatdan o'tilmagan!")
        return

    
    
    db_phone_standard = validate_phone_number(user.phone)

    await state.update_data(
        db_username=user.username, 
        db_phone=db_phone_standard
    )
    
    await state.set_state(ForgotPassword.username)
    await msg.answer(f"{i18n('enter_username')} \n <tg-spoiler>{i18n('if_username')}</tg-spoiler>", parse_mode="HTML")


@dp.message(ForgotPassword.username)
async def check_username(msg: types.Message, i18n: I18nContext, state: FSMContext):
    data = await state.get_data()
    if data.get('db_username') == msg.text:
        await state.set_state(ForgotPassword.phone)
        await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))
    else:
        await msg.answer(i18n("err_username"))


@dp.message(ForgotPassword.phone)
async def check_phone(msg: types.Message, i18n: I18nContext, state: FSMContext):
    data = await state.get_data()
    
    raw_phone = msg.contact.phone_number if msg.contact else msg.text
    validated_input = validate_phone_number(raw_phone)

    if validated_input and validated_input == data.get('db_phone'):
        await state.set_state(ForgotPassword.new_password)
        await msg.answer(i18n("set_new_password"), reply_markup=types.ReplyKeyboardRemove())
    else:
        await msg.answer(i18n("err_phone"))

@dp.message(ForgotPassword.new_password)
async def set_new_password(msg: types.Message, i18n: I18nContext, state: FSMContext):
    if len(msg.text) < 6:
        await msg.answer(i18n("invalid_password"))
        return

    await update_user_password(msg.from_user.id, msg.text)
    await msg.answer(i18n("password_changed"))
    await state.clear()