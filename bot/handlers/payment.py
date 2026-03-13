import os
import django
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram_i18n.context import I18nContext
from django.utils import timezone
from datetime import datetime, timedelta
import humanize
from dotenv import load_dotenv

from states.payment import Payment
from UI.default import payment_method, main_menu
from UI.inline import payment_version, payment_request
from accounts.models import BalanceHistory, Users, Subscription
from aiogram.types import ReplyKeyboardRemove
from asgiref.sync import sync_to_async

load_dotenv() 

payment = Router()

def get_user(tg_id):
    return Users.objects.filter(tg_id=tg_id).first()
    


def save_to_user_history(user, transaction_type, amount, description):
    BalanceHistory.objects.create(
        user=user,
        transaction_type=transaction_type,
        amount=amount,
        description=description
    )


def change_user_version(user, plan, days=30):
    sub, created = Subscription.objects.get_or_create(user=user)
    
    sub.plan = plan
    
    sub.expires_at = timezone.now() + timedelta(days=days)
    
    
    sub.save()
    return sub


@payment.message(lambda msg, i18n: msg.text == i18n("payment"))
async def payment_start(msg: types.Message, i18n: I18nContext, state: FSMContext):
    await msg.answer(i18n("att_pay"), reply_markup=ReplyKeyboardRemove())
    await msg.answer(i18n("choose_version"), reply_markup=payment_version())
    await state.set_state(Payment.version)

@payment.callback_query(Payment.version, F.data.in_(["go", "pro", "ultima"]))
async def plan_select(callback: types.CallbackQuery, i18n: I18nContext, state: FSMContext):
    await callback.message.delete()
    await state.update_data(version=callback.data)
    
    await callback.answer(i18n("selected"))
    await callback.message.answer(i18n("select_payment_method"), reply_markup=payment_method(i18n))
    await state.set_state(Payment.payment_method)

@payment.message(Payment.payment_method)
async def payment_method_session(msg: types.Message, i18n: I18nContext, state: FSMContext):
    buy_from_bal_text = i18n('buy_from_balance')
    kb_map = {
        'UZUM bank 🍇, (VISA, Mastercard)': 'VISA',
        'Uzcard, Humo': 'UZCARD',
        buy_from_bal_text:'balance'
    }

    if msg.text not in kb_map:
        await msg.answer(i18n("use_kb"), reply_markup=payment_method(i18n))
        return

    
    data = await state.get_data()
    plan = data.get('version')
    
    amount_str = os.getenv(f'PAYMENT_VALUE_{plan.upper()}')
    
    if not amount_str:
        await msg.answer(i18n("payment_failed"), reply_markup=main_menu(i18n))
        await state.clear()
        return

    method = kb_map[msg.text]
    card_number = os.getenv(method) 
    
    if method == 'balance':
        user = await sync_to_async(get_user)(msg.from_user.id)
        amount_int = int(amount_str)

        if user.balance >= amount_int:
            user.balance -= amount_int
            await sync_to_async(user.save)()

            await sync_to_async(change_user_version)(user, plan.upper(), 30)

            await sync_to_async(save_to_user_history)(
                user, 
                BalanceHistory.TransactionType.EXPENSE, 
                amount_int, 
                f"Balans orqali {plan} sotib olindi"
            )

            await msg.answer(i18n('check_accepted'), reply_markup=main_menu(i18n))
            await state.clear()
            return
        else:
            await msg.answer(i18n('insufficient_funds'), reply_markup=main_menu(i18n))
            await state.clear()
            return
    
    if method == 'VISA':
        holder_name = os.getenv("VISA_CARD_HOLDER_NAME")
    else:
        holder_name = os.getenv("UZCARD_HOLDER_NAME")
    
    header_key = 'card_for_payment_visa' if method == 'VISA' else 'card_for_payment_uz'

    try:
        formatted_amount = humanize.intcomma(int(amount_str))
    except:
        formatted_amount = amount_str

    response_text = (
        f"<b>{i18n(header_key)}:</b>\n\n"
        f"💳 <code>{card_number}</code>\n"
        f"👤 <b>{holder_name}</b>\n"
        f"💰 <b>{formatted_amount} UZS</b> {i18n(f'for_{plan}')}\n\n"
        f"<i>{i18n('send_cheque')}</i>"
    )
    await state.update_data(method=msg.text)
    await state.update_data(amount=formatted_amount)
    await msg.answer(response_text, parse_mode="HTML")
    await state.set_state(Payment.cheque)
    

@payment.message(Payment.cheque, F.photo)
async def check_cheque(msg: types.Message, i18n: I18nContext, state: FSMContext, bot: Bot):
    
    photo = msg.photo[-1].file_id
    admin = os.getenv('SUPER_ADMIN')
    data = await state.get_data()
    txt = (
    f"👤 User ID: {msg.from_user.id}\n"
    f"🏷 Username: @{msg.from_user.username}\n"
    f"📱 Versiya so'rovi: {data.get('version')}\n"
    f"💳 To'lov usuli: {data.get('method')}\n\n"
    f"GO versiya uchun to'lov: {os.getenv('PAYMENT_VALUE_GO')}\n"
    f"PRO versiya uchun to'lov: {os.getenv('PAYMENT_VALUE_PRO')}\n"
    f"ULTIMA versiya uchun to'lov: {os.getenv('PAYMENT_VALUE_ULTIMA')}\n"
)
    
    
    await bot.send_photo(admin, photo=photo, caption=txt, reply_markup=payment_request(msg.from_user.id))
    await msg.answer(i18n('cheque_proccess'), reply_markup=main_menu(i18n))
    

@payment.callback_query(F.data.startswith('accept_'))
async def accept_request_payment(call: types.CallbackQuery, i18n: I18nContext, state: FSMContext, bot: Bot):
    data_parts = call.data.split("_")
    
    if data_parts[1] == 'payment':
        await call.answer("Eski tugma! Iltimos yangi to'lovni kuting.", show_alert=True)
        return

    user_id = int(data_parts[1])
    user_id = int(call.data.split("_")[1])
    await call.message.delete()
    data = await state.get_data()
    subs_expirement = 30
    amount = data.get('amount')
    amount_str = str(amount).replace(" ", "").replace(',', '')
    user = await sync_to_async(get_user)(user_id)
    amount_int= int(amount_str)
    await sync_to_async(save_to_user_history)(user, BalanceHistory.TransactionType.EXPENSE, amount_int, f"Sizning bank kartangizdan chiqim {data.get('version')} uchun")
    version = data.get('version')
    
    if version == 'go':
        await sync_to_async(change_user_version)(user, Subscription.PlanChoices.GO, subs_expirement)
    elif version == 'pro':
        await sync_to_async(change_user_version)(user, Subscription.PlanChoices.PRO, subs_expirement)
    elif version == 'ultima':
        await sync_to_async(change_user_version)(user, Subscription.PlanChoices.ULTIMA, subs_expirement)
        
    await state.clear()
    await bot.send_message(user_id, i18n('check_accepted'), reply_markup=main_menu(i18n), message_effect_id='5046509860389126442')
    

@payment.callback_query(F.data.startswith('decline_'))
async def decline_request_payment(call: types.CallbackQuery, i18n: I18nContext, state: FSMContext, bot: Bot):
    user_id = int(call.data.split("_")[1])
    await call.message.delete()
    user = await sync_to_async(get_user)(user_id)
    await sync_to_async(save_to_user_history)(user, BalanceHistory.TransactionType.EXPENSE, 500, "Soxta chek uchun jarima !")
    state.clear()
    await bot.send_message(user_id, i18n('check_declined'), reply_markup=main_menu(i18n))
    