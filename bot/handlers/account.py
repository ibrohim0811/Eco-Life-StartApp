import sys
import os
import django
import humanize

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from django.db.models import Sum, Q
from aiogram import Router, types, F
from asgiref.sync import sync_to_async
from middleware.i18n import i18n_middleware
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram_i18n.context import I18nContext


from accounts.models import Users, BalanceHistory
from UI.inline import update


acc = Router()

def get_user_info(tg_id):
    user = Users.objects.filter(tg_id=tg_id).first()
    return user


@acc.message(lambda message, i18n: message.text == i18n('acc'))
async def about_account(msg: types.Message, i18n: I18nContext):
    user = await sync_to_async(get_user_info)(msg.from_user.id)
    await sync_to_async(lambda: user.subscription.check_subscription_status())()
    
    if user: 
        uuid = str(user.uuid).split('-')[-1]
        text = (
            f"🎯 {user.subscription.badge_text()}\n"
            f"🪪 {i18n('uuid')}: {uuid} \n"
            f"👤 {i18n('first_name')}: {user.first_name} \n\n"
            f"📃 {i18n('last_name')}: {user.last_name}\n\n"
            f"👤 {i18n('user_name')}: <code>{user.username}</code>\n\n"
            f"📞 {i18n('tel')}: {user.phone}\n\n"
            f"🌐 {i18n('til')}: {user.language}\n\n"
            f"📝 {i18n('about')}: {user.about or '-'}\n\n"
            f"💰 {i18n('balance')}: {humanize.intcomma(user.balance)} UZS"
        )
        
        await msg.answer(text, parse_mode="HTML", reply_markup=update(i18n))
       
    
    
@acc.callback_query(lambda c: c.data == "refresh")
async def refresh_account(callback: types.CallbackQuery, i18n: I18nContext):
    
    user = await sync_to_async(get_user_info)(callback.from_user.id)
    uid = str(user.uuid).split('-')[-1]
    await sync_to_async(lambda: user.subscription.check_subscription_status())()

    if user:
        new_text = (
            f"🎯 {user.subscription.badge_text()}\n"
            f"🪪 {i18n('uuid')}: {uid} \n"
            f"👤 {i18n('first_name')}: {user.first_name} \n\n"
            f"📃 {i18n('last_name')}: {user.last_name}\n\n"
            f"👤 {i18n('user_name')}: <code>{user.username}</code>\n\n"
            f"📞 {i18n('tel')}: {user.phone}\n\n"
            f"🌐 {i18n('til')}: {user.language}\n\n"
            f"📝 {i18n('about')}: {user.about or '-'}\n\n"
            f"💰 {i18n('balance')}: {humanize.intcomma(user.balance)} uzs"
        )
        
        try:
            await callback.message.edit_text(
                new_text, 
                reply_markup=update(i18n), parse_mode="HTML"
            )
        except Exception:
            pass
            
    await callback.answer(i18n("updated"))
    
# @acc.callback_query(lambda c: c.data == "change")
# async def change_info(callback: types.CallbackQuery, i18n: I18nContext):
#     await callback.answer(i18n("info_change"))