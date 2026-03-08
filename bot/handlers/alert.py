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


@dp.message(lambda message, i18n: message.text == i18n('eco_damage'))
async def start_alert(msg: types.Message, i18n: I18nContext, state: FSMContext):
    pass