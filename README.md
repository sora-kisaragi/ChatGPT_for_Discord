# Discord ChatGPT/Ollama Bot

OpenAI ChatGPT API と Ollama API の両方に対応した Discord Bot です。

## 特徴

- **複数AI対応**: OpenAI ChatGPT と Ollama の両方をサポート
- **チャンネル別会話管理**: チャンネルごとに独立した会話履歴
- **設定可能なプロンプト**: チャンネルごとにAIの設定をカスタマイズ
- **環境変数による設定**: 安全で簡単な設定管理
- **エラーハンドリング**: 堅牢なエラー処理とログ機能
- **コマンドサポート**: 豊富なボットコマンド

## 必要条件

- Python 3.8以上
- Discord Bot Token
- OpenAI API Key (OpenAI使用時) または Ollama サーバー (Ollama使用時)

## インストール

1. リポジトリをクローン
```bash
git clone <repository-url>
cd ChatGPT_for_Discord
```

2. 依存関係をインストール
```bash
pip install -r requirements.txt
```

3. 環境設定
```bash
cp .env.example .env
# .env ファイルを編集して設定を記入
```

## 設定

### 環境変数設定 (.env ファイル)

```env
# Discord設定
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_IDS=123456789012345678,987654321098765432

# AI プロバイダー設定
AI_PROVIDER=ollama  # "openai" または "ollama"

# OpenAI設定 (AI_PROVIDER=openai の場合)
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-3.5-turbo

# Ollama設定 (AI_PROVIDER=ollama の場合)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# 共通AI設定
MAX_HISTORY=10
TEMPERATURE=0.7
```

### Ollama セットアップ

1. [Ollama](https://ollama.ai/) をインストール
2. モデルをダウンロード:
```bash
ollama pull llama3.1
```
3. サーバーを起動:
```bash
ollama serve
```

## 実行

```bash
python src/ChatGPT_Discord.py
```

## 使用方法

### 基本コマンド

- `/gpt [メッセージ]` または `/ai [メッセージ]` - AIと対話
- `/reset` - 会話履歴をリセットし、設定を変更
- `/show` - 現在の設定を表示
- `/stats` - 会話統計を表示
- `/help` - ヘルプを表示

### 使用例

```
/ai こんにちは
/gpt 今日の天気はどうですか？
/reset
/show
/stats
```

## プロジェクト構造

```
ChatGPT_for_Discord/
├── src/
│   └── ChatGPT_Discord.py     # メインボットファイル
├── config.py                  # 設定管理
├── ai_client.py              # AI API クライアント
├── conversation_manager.py   # 会話履歴管理
├── utils.py                  # ユーティリティ関数
├── requirements.txt          # 依存関係
├── .env.example             # 環境変数テンプレート
└── README.md                # このファイル
```

## 主な改善点

1. **アーキテクチャの改善**
   - モジュール化とクラスベース設計
   - 関心の分離
   - 再利用可能なコンポーネント

2. **AI API 対応**
   - OpenAI と Ollama の統一インターフェース
   - 設定による動的切り替え
   - 非同期処理対応

3. **セキュリティ強化**
   - 環境変数による設定管理
   - API キーの安全な保存

4. **エラーハンドリング**
   - 包括的なエラー処理
   - ログ機能
   - ユーザーフレンドリーなエラーメッセージ

5. **機能拡張**
   - チャンネル別会話管理
   - 統計情報表示
   - タイムアウト処理

## ライセンス

このプロジェクトは[MITライセンス](LICENSE.md)のもとで公開されています。

## 貢献

プルリクエストやイシューの報告を歓迎します。