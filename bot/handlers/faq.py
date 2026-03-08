import sys
import os
import django


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Ecolife.settings")
django.setup()

from pathlib import Path
from asgiref.sync import sync_to_async
from aiogram import Router, types, F
from aiogram.types import FSInputFile
from accounts.models import Users
from aiogram_i18n.context import I18nContext


faq = Router()

current_file_path = Path(__file__).resolve()
BOT_DIR = current_file_path.parent.parent

@faq.message(F.text == "FAQ")
async def faqsend(msg: types.Message, i18n: I18nContext):
    user = await sync_to_async(Users.objects.filter(tg_id=msg.from_user.id).first)()
    lang = user.language if user and user.language else "uz"
    await i18n.set_locale(lang)

    
    file_path = file_path = BOT_DIR / "FAQ" / lang / "FAQ.docx"

    if file_path.exists():
        file = FSInputFile(path=str(file_path), filename="FAQ.docx")
        await msg.answer_document(file, caption=i18n("faq_msg"))
    else:
        print(f"Xato! Manzil topilmadi: {file_path}")
        await msg.answer("Fayl topilmadi.")
    
    
            