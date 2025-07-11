#!/bin/bash

# Discord Bot 起動スクリプト

echo "Discord ChatGPT/Ollama Bot を起動しています..."

# 仮想環境の確認
if [ ! -d ".venv" ]; then
    echo "仮想環境が見つかりません。作成しています..."
    python -m venv .venv
fi

# 仮想環境をアクティベート (Linux/Mac)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "仮想環境をアクティベートしました"
elif [ -f ".venv/Scripts/activate" ]; then
    # Windows (Git Bash)
    source .venv/Scripts/activate
    echo "仮想環境をアクティベートしました"
else
    echo "仮想環境のアクティベートに失敗しました"
    exit 1
fi

# 依存関係のインストール
echo "依存関係を確認しています..."
pip install -r requirements.txt

# .envファイルの確認
if [ ! -f ".env" ]; then
    echo "警告: .env ファイルが見つかりません"
    echo ".env.example をコピーして設定してください"
    echo ""
    echo "cp .env.example .env"
    echo ""
    exit 1
fi

# ボットを起動
echo "ボットを起動しています..."
python src/ChatGPT_Discord.py
