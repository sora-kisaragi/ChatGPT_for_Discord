@echo off
cd /d "D:\Program Files\VSCode\ChatGPT_for_Discord"
call .venv\Scripts\activate.bat
python src\discord_ai_bot.py
pause