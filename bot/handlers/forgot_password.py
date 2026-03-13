import re
import sys
import os
import django
import random
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from dotenv import load_dotenv
from states.forgot import ForgotPassword
from asgiref.sync import sync_to_async
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from accounts.models import Users
from aiogram_i18n.context import I18nContext
from aiogram.types import ReplyKeyboardRemove
from UI.default import contact_button
from validation.validate import validate_phone_number
from django.contrib.auth.hashers import make_password
from accounts.tasks import send_sms_task
from UI.default import main_menu, back
from django.utils import timezone
from accounts.models import UserActivities

dp = Router()

@sync_to_async
def get_user_by_tg_id(tg_id):
    return Users.objects.filter(tg_id=tg_id).first()

@sync_to_async
def update_user_password(tg_id, new_password):
    return Users.objects.filter(tg_id=tg_id).update(password=new_password)

def is_strong_password(password: str) -> bool:
    """Parol kamida 8 ta belgi, 1 ta raqam va 1 ta katta harfdan iboratligini tekshiradi."""
    if len(password) < 8:
        return False
    if not re.search(r"\d", password): 
        return False
    if not re.search(r"[A-Z]", password): 
        return False
    return True

@sync_to_async
def update_user_password(tg_id, new_password):
    return Users.objects.filter(tg_id=tg_id).update(password=new_password)

load_dotenv()

TOKEN = os.getenv("SMS_API")
BASE_URL = "https://devsms.uz/api"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def get_user(tg_id):
    return Users.objects.select_related('subscription').filter(tg_id=tg_id).first() 

def check_user_limit_sync(tg_id):
    user = Users.objects.select_related('subscription').filter(tg_id=tg_id).first()
    if not user:
        return None, 0, "FREE" 
        
    today = timezone.now().date()
    today_count = UserActivities.objects.filter(
        user__phone=user.phone, 
        created_at__date=today
    ).count()
    
    return user, today_count, user.subscription.badge_text()

FREE_LIMIT = 1
GO_LIMIT = 1
PRO_LIMIT = 2
ULTIMA_LIMIT = 3


@dp.message(lambda message, i18n: message.text == i18n('forgot_password'))
async def forgot_password_start(msg: types.Message, i18n: I18nContext, state: FSMContext):
    
    user, today_count, badge = await sync_to_async(check_user_limit_sync)(tg_id=msg.from_user.id)
    
    if badge == 'FREE' and today_count >= FREE_LIMIT:
        await msg.answer(i18n('limit_reached'))
        return
    elif badge == 'GO' and today_count >= GO_LIMIT:
        await msg.answer(i18n('limit_reached'))
        return
    elif badge == 'PRO' and today_count >= PRO_LIMIT:
        await msg.answer(i18n('limit_reached'))
        return
    elif badge == 'ULTIMA' and today_count >= ULTIMA_LIMIT:
        await msg.answer(i18n('limit_reached'))
        return
    
    user = await get_user_by_tg_id(msg.from_user.id)
    if not user:
        await msg.answer(i18n('non_registered'))
        return
    
    await state.update_data(
        db_username=user.username,
        db_phone=validate_phone_number(user.phone),
        attempts=0  
    )
    
    await state.set_state(ForgotPassword.username)
    await msg.answer(i18n('enter_username'), reply_markup=back())




@dp.message(ForgotPassword.username)
async def check_username(msg: types.Message, i18n: I18nContext, state: FSMContext):
    data = await state.get_data()
    attempts = data.get('attempts', 0)

    if attempts >= 3:
        await msg.answer(i18n("nw_p_try_again"))
        await state.clear()
        return

    if data.get('db_username') == msg.text.strip():
        otp_code = str(random.randint(100000, 999999))
        user_phone = data.get('db_phone')   
        
        
        send_sms_task.delay(user_phone, f"EcoLife platformasiga kirish uchun tasdiqlash kodi: {otp_code}. Kodni hech kimga bermang.")
        
        print(f"DEBUG: OTP yuborildi {user_phone} -> {otp_code}")
        
        await state.update_data(otp_code=otp_code)
        await state.set_state(ForgotPassword.phone) 
        await msg.answer(i18n("phone"), reply_markup=contact_button(i18n))
    else:
        new_attempts = attempts + 1
        await state.update_data(attempts=new_attempts)
        await msg.answer(f"{i18n('err_username')} ({i18n('try_validate')}: {3 - new_attempts})")

@dp.message(ForgotPassword.phone)
async def check_phone(msg: types.Message, i18n: I18nContext, state: FSMContext):
    data = await state.get_data()
    raw_phone = msg.contact.phone_number if msg.contact else msg.text
    validated_input = validate_phone_number(raw_phone)

    if validated_input == data.get('db_phone'):
        await state.set_state(ForgotPassword.otp_verify) 
        await msg.answer(i18n("enter_otp"))
    else:
        await msg.answer(i18n("err_phone"))

@dp.message(ForgotPassword.otp_verify) 
async def verify_otp(msg: types.Message, i18n: I18nContext, state: FSMContext):
    data = await state.get_data()
    
    if msg.text == data.get('otp_code'):
        await state.set_state(ForgotPassword.new_password)
        await msg.answer(i18n("success_sms"))
    else:
        await msg.answer(i18n("invalid_otp"))

@dp.message(ForgotPassword.new_password)
async def set_new_password(msg: types.Message, i18n: I18nContext, state: FSMContext):
    if not is_strong_password(msg.text):
        await msg.answer(i18n("invalid_password"))
        return

    hashed_password = make_password(msg.text)
    await update_user_password(msg.from_user.id, hashed_password)
    
    await msg.answer(i18n("password_changed"), reply_markup=main_menu(i18n))
    await state.clear()