@echo off
:: Django uchun
start cmd /k "call venv/Scripts/activate && python manage.py runserver"

:: Bot uchun
start cmd /k "call venv/Scripts/activate && python bot/main.py"