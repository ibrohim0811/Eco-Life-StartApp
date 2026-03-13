# from pathlib import Path
# import os
# from dotenv import load_dotenv

# load_dotenv()

# BASE_DIR = Path(__file__).resolve().parent.parent 
# env_path = BASE_DIR / '.env'

# load_dotenv(dotenv_path=env_path)

# TOKEN = os.getenv("BOT_TOKEN")
# print("debug", TOKEN)




#  downloaded_file = await bot.download_file(file_info.file_path)
    
#     base64_image = base64.b64encode(downloaded_file.read()).decode('utf-8')

#     client = OpenAI(
#         api_key=os.getenv('GROQ_API_KEY'),
#         base_url="https://api.groq.com/openai/v1"
#     )

#     try:
#         processing_msg = await msg.answer("Chek tahlil qilinmoqda...")

#         response = client.chat.completions.create(
#             model="llama-3.2-11b-vision-preview", 
#             messages=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "text", "text": "Bu to'lov chekimi? Agar chek bo'lsa, undagi summa va sanani aniqla. Faqat 'ha' yoki 'yo'q' deb javob berma, qisqacha ma'lumot ber."},
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": f"data:image/jpeg;base64,{base64_image}",
#                             },
#                         },
#                     ],
#                 }
#             ],
#         )

#         analysis_result = response.choices[0].message.content
#         print(analysis_result) 

        
#         await processing_msg.delete()
#         await msg.answer(f"Tahlil natijasi: \n\n{analysis_result}")
        
        
#         await state.clear()

#     except Exception as e:
#         print(f"Xatolik: {e}")
#         await msg.answer("Chekni tahlil qilishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")