import asyncio
import logging
import os
from aiogram import Router, Bot, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError, TelegramBadRequest
from aiogram.types import FSInputFile
from dotenv import load_dotenv




load_dotenv()

dp_admin = Router()


import psycopg2
from psycopg2.extras import DictCursor

DB_PARAMS = {
    "host": "localhost",
    "port": "5432",
    "database": "Eco Life",
    "user": "postgres",
    "password": "ibrohim0811"
}


def get_all_users_from_db():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor(cursor_factory=DictCursor)
    
    # Kerakli ustunlarni tanlab olamiz
    query = "SELECT id, telegram_id, username, first_name, is_active, phone, uuid, balance, password, date_joined FROM app_user ORDER BY date_joined DESC"
    cur.execute(query)
    users = cur.fetchall()
    
    cur.close()
    conn.close()
    return users


def get_all_tg_ids():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT telegram_id FROM app_user")
    ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return ids




import psycopg2

def get_user_info(tg_id):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    query = """
        SELECT district, first_name, username, balance, phone
        FROM app_user
        WHERE telegram_id = %s
        LIMIT 1
    """
    cur.execute(query, (tg_id,))
    row = cur.fetchone()

    # DEBUG (hozircha tekshirish uchun)
    print("ROW TYPE:", type(row), "ROW:", row)

    cur.close()
    conn.close()

    if row is None:
        return None

    # row bu tuple: (district, first_name, username, balance, phone)
    return {
        "district": row[0],
        "first_name": row[1],
        "username": row[2],
        "balance": row[3],
        "phone": row[4],
    }



def get_user_image(tg_id):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    
    query = "SELECT image FROM app_user WHERE telegram_id = %s LIMIT 1"
    cur.execute(query, (tg_id,))
    row = cur.fetchone()

    cur.close()
    conn.close()

    if row is None:
        return None

    return row[0] 



class AdminStates(StatesGroup):
    waiting_broadcast_type = State()
    waiting_broadcast_content = State() 


ADMIN_IDS = [int(os.getenv("SUPER_ADMIN", 0))]
TOKEN = os.getenv("BOT_TOKEN")

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@dp_admin.message(Command("send_message"))
async def cmd_send_message(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Bu buyruq faqat admin uchun!")
        return

    await state.clear()
    await state.set_state(AdminStates.waiting_broadcast_type)

    kb = InlineKeyboardBuilder()
    kb.button(text="📝 Matn", callback_data="broadcast:text")
    kb.button(text="🖼 Rasm", callback_data="broadcast:photo")
    kb.button(text="🎞 Video", callback_data="broadcast:video")
    kb.adjust(1)

    await message.answer(
        "Qaysi turdagi xabar yuborasiz?\n\nBekor qilish uchun /cancel",
        reply_markup=kb.as_markup(),
    )

@dp_admin.callback_query(AdminStates.waiting_broadcast_type, F.data.startswith("broadcast:"))
async def cb_broadcast_type(callback: types.CallbackQuery, state: FSMContext):
    kind = callback.data.split(":")[1]
    await state.update_data(broadcast_kind=kind)
    
    await state.set_state(AdminStates.waiting_broadcast_content)
    
    texts = {
        "text": "📝 Matn yuboring.",
        "photo": "🖼 Rasm yuboring (izoh bilan bo'lishi mumkin).",
        "video": "🎞 Video yuboring (izoh bilan bo'lishi mumkin)."
    }
    
    await callback.message.edit_text(texts.get(kind, "Xabarni yuboring"))
    await callback.answer()

@dp_admin.message(Command("cancel"))
async def cmd_cancel_broadcast(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.clear()
    await message.answer("❌ Amaliyot bekor qilindi.")

async def _broadcast_send(bot: Bot, kind: str, message: types.Message) -> tuple[int, int]:
    user_ids = get_all_tg_ids()
    ok, fail = 0, 0
    
    for uid in user_ids:
        try:
            if kind == "text":
                await bot.send_message(uid, message.text)
            elif kind == "photo":
                await bot.send_photo(uid, photo=message.photo[-1].file_id, caption=message.caption)
            elif kind == "video":
                await bot.send_video(uid, video=message.video.file_id, caption=message.caption)
            
            ok += 1
            await asyncio.sleep(0.05) #
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except (TelegramForbiddenError, TelegramBadRequest):
            fail += 1
        except Exception as e:
            logging.error(f"Xato {uid}: {e}")
            fail += 1
    return ok, fail

@dp_admin.message(AdminStates.waiting_broadcast_content)
async def handle_broadcast_content(message: types.Message, state: FSMContext, bot: Bot):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    kind = data.get("broadcast_kind")

    # To'g'ri format yuborilganini tekshirish
    if kind == "text" and not message.text:
        return await message.answer("Iltimos, faqat matn yuboring.")
    if kind == "photo" and not message.photo:
        return await message.answer("Iltimos, rasm yuboring.")
    if kind == "video" and not message.video:
        return await message.answer("Iltimos, video yuboring.")

    sent_msg = await message.answer("⏳ Tarqatish boshlandi...")
    ok, fail = await _broadcast_send(bot, kind, message)
    
    await state.clear()
    await sent_msg.edit_text(f"✅ Yakunlandi!\n\nmuvaffaqiyatli: {ok}\nXato: {fail}")
    
    
from fpdf import FPDF

def generate_users_pdf(users_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "Foydalanuvchilar Ro'yxati", ln=True, align='C')
    pdf.ln(10) # Bo'sh joy

    # Jadval sarlavhasi
    pdf.set_font("Arial", "B", 10)
    pdf.cell(10, 8, "No", 1)
    pdf.cell(30, 8, "TG ID", 1)
    pdf.cell(50, 8, "Username", 1)
    pdf.cell(60, 8, "Ism", 1)
    pdf.cell(40, 8, "Sana", 1)
    pdf.ln()

    # Ma'lumotlarni to'ldirish
    pdf.set_font("Arial", "", 9)
    for idx, user in enumerate(users_data, 1):
        pdf.cell(10, 8, str(idx), 1)
        pdf.cell(30, 8, str(user['telegram_id']), 1)
        pdf.cell(50, 8, str(user['username'] or "N/A"), 1)
        pdf.cell(60, 8, str(user['first_name'][:30]), 1) # Ism juda uzun bo'lsa qirqamiz
        joined_date = user.get('date_joined')
        sana_matni = joined_date.strftime('%Y-%m-%d') if joined_date else "N/A"
        pdf.cell(40, 8, sana_matni, 1)
        pdf.ln()

    file_path = "all_users.pdf"
    pdf.output(file_path)
    return file_path


import sys
import datetime
from fpdf import FPDF

# Terminal xabarlarini saqlash uchun vaqtinchalik xotira
import sys
import os
import datetime
import logging
import asyncio
from fpdf import FPDF
from aiogram import Router, Bot, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import FSInputFile

# --- 1. TERMINAL LOGLARINI TUTISH TIZIMI ---
terminal_logs = []

class TerminalLogger:
    def __init__(self, original_stream):
        self.stream = original_stream

    def write(self, message):
        self.stream.write(message)
        if message.strip():
            # Vaqtni qo'shish va belgilarni tozalash (PDF xato bermasligi uchun)
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            # ASCII bo'lmagan belgilarni (emoji va h.k) olib tashlaymiz
            clean_msg = message.strip().encode('ascii', 'ignore').decode('ascii')
            terminal_logs.append(f"[{timestamp}] {clean_msg}")

    def flush(self):
        self.stream.flush()

# stdout va stderr ni yo'naltirish (Barcha loglarni tutish uchun)
sys.stdout = TerminalLogger(sys.stdout)
sys.stderr = TerminalLogger(sys.stderr)

# Loggingni bizning TerminalLogger orqali o'tadigan qilish
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stdout,
    format="%(levelname)s:%(name)s:%(message)s"
)


dp_admin = Router()
ADMIN_IDS = [int(os.getenv("SUPER_ADMIN", 0))] # .env dan olingan ID

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

class AdminStates(StatesGroup):
    waiting_broadcast_content = State()

# --- 3. PDF GENERATSIYA FUNKSIYALARI ---

def save_terminal_to_pdf():
    """Terminal loglarini qora fonda oq matn qilib PDFga saqlaydi"""
    if not terminal_logs:
        return None

    pdf = FPDF()
    pdf.add_page()
    
    # Qora fon
    pdf.set_fill_color(0, 0, 0)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Oq matn va terminal shrifti
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Courier", size=8)
    
    pdf.cell(0, 10, txt="--- TERMINAL LOG SESSION ---", ln=True, align='C')
    pdf.ln(5)
    
    y_pos = 20
    # Faqat oxirgi 100 ta qatorni chiqaramiz
    for line in terminal_logs[-100:]:
        if y_pos > 275: # Yangi sahifa
            pdf.add_page()
            pdf.set_fill_color(0, 0, 0)
            pdf.rect(0, 0, 210, 297, 'F')
            y_pos = 10
        
        pdf.cell(0, 5, txt=f"> {line}", ln=True)
        y_pos += 5
    
    file_name = f"logs/terminal_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
    os.makedirs("logs", exist_ok=True)
    pdf.output(file_name)
    return file_name



import datetime

@dp_admin.message(Command("log"))
async def cmd_get_terminal_log(message: types.Message):
    """Terminal loglarini PDF ko'rinishida yuboradi"""
    if not is_admin(message.from_user.id):
        return

    # Tekshiruv uchun bitta log yozamiz
    print(f"Admin {message.from_user.id} log so'radi.")
    
    status_msg = await message.answer("🔄 PDF tayyorlanmoqda...")
    
    try:
        pdf_path = save_terminal_to_pdf()
        if pdf_path:
            document = FSInputFile(pdf_path)
            await message.answer_document(
                document, 
                caption=f"📄 Terminal loglari\nVaqt: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            await status_msg.delete()
        else:
            await status_msg.edit_text("📭 Terminal xotirasi bo'sh.")
    except Exception as e:
        logging.error(f"PDF xatosi: {e}")
        await status_msg.edit_text(f"❌ Xatolik yuz berdi: {e}")

@dp_admin.message(Command("clear_logs"))
async def cmd_clear_logs(message: types.Message):
    """Xotiradagi loglarni tozalaydi"""
    if not is_admin(message.from_user.id):
        return
    terminal_logs.clear()
    await message.answer("🧹 Terminal xotirasi tozalandi.")

# --- TEST PRINT ---
print(">>> SYSTEM: Terminal monitoring v2.0 activated.")
print(f">>> ADMINS: {ADMIN_IDS}")