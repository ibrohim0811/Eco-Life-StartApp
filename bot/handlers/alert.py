import sys
import os
import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()


from aiogram import Router, types, F, Bot
from asgiref.sync import sync_to_async
from middleware.i18n import i18n_middleware
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from django.db import transaction
from aiogram.types import ReplyKeyboardRemove

from aiogram_i18n.context import I18nContext
from bot.connections import get_user_language
from states.alert import EcoALert

from UI.default import send_location
from accounts.models import UserActivities, BalanceHistory
from UI.default import main_menu
from UI.inline import sorov
from connections import get_user_language, get_user

TOKEN = os.getenv("BOT_TOKEN")
ADMIN = os.getenv("SUPER_ADMIN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

dp = Router()
bot = Bot(token=TOKEN)
print(dp)


@dp.message(lambda message, i18n: message.text == i18n("eco_damage"))
async def start_alert(msg: types.Message, i18n: I18nContext, state: FSMContext):
    
    language = await sync_to_async(get_user_language)(tg_id=msg.from_user.id)
    await i18n.set_locale(language)
    await msg.answer(i18n("info_alert"))
    await msg.answer(i18n("alert_video"), reply_markup=ReplyKeyboardRemove())
    await state.set_state(EcoALert.video)
    
@dp.message(EcoALert.video)
async def get_video_save(msg: types.Message, i18n: I18nContext, state: FSMContext):
    video_file_id = None
    video_type = None
    
    if msg.video:
        video_file_id = msg.video.file_id
        video_type = "video"
    
    elif msg.video_note:
        video_file_id = msg.video_note.file_id
        video_type = "video_note"
        
    if video_file_id:
        await state.update_data(video_id=video_file_id, file_type=video_type)
        
        await msg.answer(i18n("send_location"), reply_markup=send_location(i18n))
        await state.set_state(EcoALert.location)
         
    else:
        await msg.answer(i18n("send_video"))
        await state.set_state(EcoALert.video)
        
        
@dp.message(EcoALert.location, F.location)
async def get_location(msg: types.Message, i18n: I18nContext, state: FSMContext):
    lat = msg.location.latitude
    lon = msg.location.longitude
    
    if lat and lon:
        await state.update_data(longitude=lon)
        await state.update_data(latitude=lat)
        
        
        data = await state.get_data()
        
        video_type = data.get("file_type")
        longtidute = data.get("longitude")
        latitude = data.get("latitude")
        video = data.get("video_id")
        user = await sync_to_async(get_user)(tg_id=msg.from_user.id)
        
        activity = await sync_to_async(UserActivities.objects.create)(
            user=user,
            video_file_id=video,
            longitude=longtidute,
            latitude=latitude
        )
        
        
        
        if video_type == "video":
            await bot.send_video(ADMIN, video=video, caption=f"👤 Foydalanuvchi: @{msg.from_user.username}\n Uzunlik: {longtidute}\nKenglik: {latitude}", reply_markup=sorov(activity.id))
        elif video_type == "video_note":
            await bot.send_video_note(chat_id=ADMIN, video_note=video, reply_markup=sorov(activity.id))
            
        await msg.answer(i18n("sent"), reply_markup=main_menu(i18n))
            
            
        await state.clear()
        
    else:
        await msg.answer(i18n("invalid_location"))
        await state.set_state(EcoALert.location)
        
        
@dp.callback_query(F.data.startswith("yes_"))
async def accepted(callback: types.CallbackQuery, i18n: I18nContext):
    activity_id = callback.data.split("_")[1]
    @sync_to_async
    def  process_acceptance():
        try:
            with transaction.atomic():
                activity = UserActivities.objects.select_related('user').select_for_update().get(id=activity_id)
                activity.status = activity.ProccesStatus.ACCEPTED
                
                
                
                BalanceHistory.objects.create(
                    user=activity.user,
                    amount=activity.amount,
                    transaction_type=BalanceHistory.TransactionType.INCOME,
                    description = f"#{activity_id} - ariza qabul qilindi"
                )
                
                activity.user.balance += activity.amount
                activity.user.save()
                
                return "ok", activity
        except UserActivities.DoesNotExist:
            return "not_found", None
        except Exception as e:
            print(f"system_error{e}")
            return "error", None
        
    status, activity = await process_acceptance()
    
    if status == "ok":
        if activity.video_file_id:
            try:
                await bot.send_video_note(CHANNEL_ID, activity.video_file_id)
            except Exception as e:
                print(f"Video yuborishda xato: {e}")
                
            await callback.message.delete()
            
            u_id = activity.user.tg_id 
        
            await bot.send_message(u_id, i18n("amount"), message_effect_id="5046509860389126442", reply_markup=main_menu(i18n))
            await callback.answer("Tasdiqlandi!")
                
        await callback.answer("Tasdiqlandi!")

    elif status == "already_done":
        await callback.answer("Bu ariza allaqachon tasdiqlangan!")
    else:
        await callback.answer("Ma'lumot topilmadi yoki xatolik yuz berdi!")
        

@dp.callback_query(F.data.startswith("already_"))
async def status_already(callback: types.CallbackQuery, i18n: I18nContext):
    
    lang = await sync_to_async(get_user_language)(tg_id=callback.message.from_user.id)
    await i18n.set_locale(lang)
    activity_id = callback.data.split("_")[1]
    
    def activity_status_update():
        
        
        with transaction.atomic():
            try:
            
                act = UserActivities.objects.select_related('user').get(id=activity_id)
                
                act.status = act.ProccesStatus.EXISTS
                act.save()
                return act
            except UserActivities.DoesNotExist:
                return None
            
    activity = await sync_to_async(activity_status_update)()
    
    if not activity:
        await callback.message.answer("Ariza mavjud emas")
        
    
    chat_id = activity.user.tg_id 

    try:
        await bot.send_message(
            chat_id=chat_id, 
            text=i18n("something_went_wrong"), 
            reply_markup=main_menu(i18n)
        )
        await callback.answer(i18n("something_went_wrong"), show_alert=False)
        
        await callback.message.edit_text(f"ID: {activity_id} - {i18n('something_went_wrong')}")

    except Exception as e:
        
        print(f"Telegram yuborishda xato: {e}")
        await callback.answer(
            "Baza yangilandi, lekin foydalanuvchiga xabar bormadi (Chat not found).", 
            show_alert=True
        )
                
            
    
@dp.callback_query(F.data.startswith("no_"))
async def status_already(callback: types.CallbackQuery, i18n: I18nContext):
    
    lang = await sync_to_async(get_user_language)(tg_id=callback.message.from_user.id)
    await i18n.set_locale(lang)
    activity_id = callback.data.split("_")[1]
    
    
    def activity_status_update():
        
        punishment = 750
        with transaction.atomic():
            try:
            
                act = UserActivities.objects.select_related('user').get(id=activity_id)
                
                
                act.status = act.ProccesStatus.REJECTED
                
                BalanceHistory.objects.create(
                    user=activity.user,
                    amount=punishment,
                    transaction_type=BalanceHistory.TransactionType.EXPENSE,
                    description=f"#{activity_id} - rad etildi (no'tog'ri ma'lumot yuborilgan !)"
                )
                
                act.user.balance -= punishment 
                act.save()
                return act
            except UserActivities.DoesNotExist:
                return None
            
    activity = await sync_to_async(activity_status_update)()
    
    if not activity:
        await callback.message.answer("Ariza mavjud emas")
        
    
    chat_id = activity.user.tg_id 

    try:
        await bot.send_message(
            chat_id=chat_id, 
            text=i18n("rejected"), 
            reply_markup=main_menu(i18n),
            message_effect_id="5104858069142078462"
        )
        await callback.answer(i18n("rejected"), show_alert=False)
        
        await callback.message.edit_text(f"ID: {activity_id} - {i18n('rejected')}")

    except Exception as e:
        
        print(f"Telegram yuborishda xato: {e}")
        await callback.answer(
            "Baza yangilandi, lekin foydalanuvchiga xabar bormadi (Chat not found).", 
            show_alert=True
        )