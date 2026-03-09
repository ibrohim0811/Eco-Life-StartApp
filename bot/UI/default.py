from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram_i18n import I18nContext
from aiogram.utils.i18n import I18n 


def contact_button(i18n: I18nContext) -> ReplyKeyboardMarkup:
    _ = i18n
    
    return ReplyKeyboardMarkup(
        keyboard=[
            
            [
            KeyboardButton(text=_("share_phone"), request_contact=True)
            ]
            
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    
def sorov(i18n: I18nContext) -> ReplyKeyboardMarkup:
    _ = i18n
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("register"))
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    
def main_menu(i18n: I18nContext) ->ReplyKeyboardMarkup:
    
    _ = i18n
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=i18n('eco_damage'))
            ],
            [
                KeyboardButton(text=i18n('acc'))
            ],
            [
                KeyboardButton(text=i18n('payment'))
            ],
            [
                KeyboardButton(text=i18n('forgot_password'))
            ],
            [
                KeyboardButton(text="FAQ")
            ],
        ], 
        resize_keyboard=True
    )
    
    
def payment_method_choice(i18n: I18nContext) -> ReplyKeyboardMarkup:
    
    _ = i18n
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=_("pay")),
                KeyboardButton(text=_("withdrawal"))
            ]      
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
def send_location(i18n: I18nContext) -> ReplyKeyboardMarkup:
    
    _ = i18n
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("share_location"), request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True        
    )