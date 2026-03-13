from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram_i18n import I18nContext

def settings_lang(i18n: I18nContext) -> InlineKeyboardMarkup:
   
    _ = i18n
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("uzbek"), callback_data="uz"),
                InlineKeyboardButton(text=_("rus"), callback_data="ru"),
                InlineKeyboardButton(text=_("en"), callback_data="en")
            ]
        ]
    )
    
def payment_version() -> InlineKeyboardMarkup:
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=("GO 💨"), callback_data="go"),
                InlineKeyboardButton(text=("Pro ⚡"), callback_data="pro"),
                InlineKeyboardButton(text=("Ultima 👑"), callback_data="ultima")
            ]   
        ]
    )
    
    
def payment_request(user_id: int) -> InlineKeyboardMarkup:
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text='Qabul qilish ✅', callback_data=f'accept_{user_id}'),
                InlineKeyboardButton(text='Bekor qilish ❌', callback_data=f'decline_{user_id}')
            ]
        ]
    )
    
    
def change_lang(i18n: I18nContext) -> InlineKeyboardMarkup:
   
    _ = i18n
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=_("uzbek"), callback_data="uzbek"),
                InlineKeyboardButton(text=_("rus"), callback_data="rus"),
                InlineKeyboardButton(text=_("en"), callback_data="en")
            ]
        ]
    )
    
def sorov(activity_id) -> InlineKeyboardMarkup:
    
    
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Ha ✅", callback_data=f"yes_{activity_id}"),
                InlineKeyboardButton(text="Allaqachon qabul qilingan ⚠️", callback_data=f"already_{activity_id}"),
                InlineKeyboardButton(text="Yo'q ❌", callback_data=f"no_{activity_id}"),
                
            ]
        ]
    )
    
    
    
    
def update(i18n: I18nContext) -> InlineKeyboardMarkup:
   
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=i18n("update"), callback_data="refresh"),
            ]
        ],
    )