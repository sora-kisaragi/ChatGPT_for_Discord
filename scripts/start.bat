@echo off
chcp 65001 > nul

echo Discord ChatGPT/Ollama Bot を起動しています...

REM ワーキングディレクトリを親フォルダに変更
cd /d "%~dp0.."

REM 仮想環境の確認
if not exist ".venv" (
    echo 仮想環境が見つかりません。作成しています...
    python -m venv .venv
)

REM 仮想環境をアクティベート
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 仮想環境のアクティベートに失敗しました
    pause
    exit /b 1
)
echo 仮想環境をアクティベートしました

REM 依存関係のインストール
echo 依存関係を確認しています...
pip install -r requirements.txt

REM .envファイルの確認
if not exist ".env" (
    echo 警告: .env ファイルが見つかりません
    echo config\.env.example をコピーして設定してください
    echo.
    echo copy config\.env.example .env
    echo.
    pause
    exit /b 1
)

REM ボットを起動
echo ボットを起動しています...
python src\discord_ai_bot.py

pause
