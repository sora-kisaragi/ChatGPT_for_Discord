# Discord ChatGPT/Ollama Bot 使用方法

## 概要
このボットは OpenAI ChatGPT / Ollama / Google Gemini API に対応した Discord ボットです。

## セットアップ

### 1. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 2. 環境変数設定
`.env`ファイルを作成し、以下の設定を行ってください：

```env
# Discord設定
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_IDS=channel_id1,channel_id2  # 空にすると全チャンネル

# AI プロバイダー設定
AI_PROVIDER=ollama  # "openai" / "ollama" / "gemini"

# OpenAI設定 (AI_PROVIDER=openai の場合)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# Ollama設定 (AI_PROVIDER=ollama の場合)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# 共通設定
MAX_HISTORY=10
TEMPERATURE=0.7
MAX_TOKENS=  # 空にすると制限なし

# ログレベル
LOG_LEVEL=INFO

# Gemini設定 (AI_PROVIDER=gemini の場合)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-pro
```

### 3. Ollama セットアップ（Ollamaを使用する場合）
1. [Ollama](https://ollama.ai/)をインストール
2. モデルをダウンロード：`ollama pull llama3.1`
3. Ollamaサーバーを起動：`ollama serve`

### 4. Gemini の準備（Gemini を使用する場合）
1. Google AI Studio で API キーを取得（GEMINI_API_KEY）
2. `requirements.txt` をインストール（google-generativeai を含む）
3. .env に GEMINI_API_KEY と GEMINI_MODEL を設定

## 使用方法

### 利用可能なコマンド
- `/gpt [メッセージ]` または `/ai [メッセージ]` - AIと対話
- `/reset` - 会話履歴をリセットし、設定を変更
- `/show` - 現在の設定を表示
- `/stats` - 会話統計を表示
- `/help` - ヘルプを表示

### 実行方法
```bash
python src/discord_ai_bot.py
```

または
```bash
# Windows
start.bat

# Linux/Mac
bash start.sh
```

## トラブルシューティング

### よくある問題

1. **ValueError: invalid literal for int() with base 10: ''**
   - 環境変数が空文字列になっています
   - `.env`ファイルを確認し、必要な値を設定してください

2. **Ollama API connection error**
   - Ollamaサーバーが起動しているか確認
   - `OLLAMA_BASE_URL`が正しいか確認

3. **OpenAI API error**
   - `OPENAI_API_KEY`が正しく設定されているか確認
   - APIキーに十分なクレジットがあるか確認

## ログ
ボットの動作ログは`discord_bot.log`ファイルに記録されます。
