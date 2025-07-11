"""
改良版 Discord ChatGPT/Ollama Bot
OpenAI API と Ollama API の両方に対応した Discord ボット
"""
import os
import sys
import asyncio
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import discord
from discord.ext import commands
from dotenv import load_dotenv

from config import load_config, DEFAULT_SETTING, get_channel_prompt, set_channel_prompt, delete_channel_prompt
from ai_client import create_ai_client, AIClient
from conversation_manager import ConversationManager
from utils import setup_logging, format_response_text, safe_send_message, validate_channel_access, extract_command_content

# 環境変数を読み込み
load_dotenv()

# ログ設定
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))

class ChatBot:
    """メインのボットクラス"""
    
    def __init__(self):
        # 設定読み込み
        self.ai_config, self.discord_config, self.prompt_config = load_config()
        
        # コンポーネント初期化
        self.ai_client: AIClient = create_ai_client(
            self.ai_config.provider,
            api_key=self.ai_config.openai_api_key,
            model=self.ai_config.openai_model if self.ai_config.provider == "openai" else self.ai_config.ollama_model,
            base_url=self.ai_config.ollama_base_url if self.ai_config.provider == "ollama" else None,
            temperature=self.ai_config.temperature,
            max_tokens=self.ai_config.max_tokens
        )
        
        self.conversation_manager = ConversationManager(max_history=self.ai_config.max_history)
        
        # Discord Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix='/', intents=intents)
        
        # イベントハンドラー登録
        self._setup_events()
        
        logger.info(f"Bot initialized with AI provider: {self.ai_config.provider}")
    
    def _setup_events(self):
        """イベントハンドラーを設定"""
        
        @self.bot.event
        async def on_ready():
            logger.info(f'{self.bot.user} がログインしました')
            logger.info(f'AI Provider: {self.ai_config.provider}')
            if self.discord_config.channel_ids:
                logger.info(f'監視チャンネル: {self.discord_config.channel_ids}')
            else:
                logger.info('全チャンネルを監視中')
            
            # 登録チャンネルにログインメッセージを送信
            await self._send_login_message()
        
        @self.bot.event
        async def on_message(message):

            # 📝 すべてのメッセージをログに記録
            logger.info(f"[MESSAGE] Server: {message.guild.name if message.guild else 'DM'} | "
                       f"Channel: #{message.channel.name if hasattr(message.channel, 'name') else 'DM'} ({message.channel.id}) | "
                       f"Author: {message.author} ({message.author.id}) | "
                       f"Bot: {message.author.bot} | "
                       f"Content: {message.content}")

            if message.author.bot:
                return
            
            # チャンネル権限確認
            if not validate_channel_access(message.channel.id, self.discord_config.channel_ids):
                return
            
            await self._handle_message(message)
    
    async def _handle_message(self, message):
        """メッセージ処理のメインロジック"""
        channel = message.channel
        channel_id = channel.id
        
        try:
            # コマンド処理
            content = message.content.strip()
            if content.startswith('/reset'):
                await self._handle_reset_command(message)
            elif content.startswith('/show'):
                await self._handle_show_command(message)
            elif content.startswith('/stats'):
                await self._handle_stats_command(message)
            elif content.startswith('/help'):
                await self._handle_help_command(message)
            elif content.startswith('/setting'):
                await self._handle_setting_command(message)
            elif content.startswith('/gpt') or content.startswith('/ai'):
                await self._handle_ai_command(message)
            elif content.startswith('/'):
                # 不明なコマンド
                await safe_send_message(
                    channel, 
                    "不明なコマンドです。`/help` で利用可能なコマンドを確認してください。"
                )
        
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await safe_send_message(
                channel, 
                "申し訳ございません。処理中にエラーが発生いたしました。管理者にお問い合わせください。"
            )
    
    async def _handle_reset_command(self, message):
        """リセットコマンドの処理"""
        channel = message.channel
        channel_id = channel.id
        
        await safe_send_message(
            channel, 
            'AIを初期化します。\n設定を変更する場合は新しい設定を送信してください。\n設定を変更しない場合は `/default` を入力してください。'
        )
        
        def check(m):
            return m.author == message.author and m.channel == channel
        
        try:
            msg = await self.bot.wait_for('message', check=check, timeout=300.0)  # 5分タイムアウト
            
            if msg.content == "/default":
                # チャンネル固有の設定があればそれを使用、なければデフォルト設定
                new_setting = get_channel_prompt(channel_id, self.prompt_config)
            else:
                new_setting = msg.content
            
            self.conversation_manager.reset_conversation(channel_id, new_setting)
            
            await safe_send_message(channel, "初期化を行いました。")
            logger.info(f"Channel {channel_id}: Conversation reset")
            
        except asyncio.TimeoutError:
            await safe_send_message(channel, "タイムアウトしました。リセットをキャンセルします。")
    
    async def _handle_show_command(self, message):
        """設定表示コマンドの処理"""
        channel_id = message.channel.id
        current_setting = self.conversation_manager.get_system_setting(channel_id)
        
        show_text = f"""⚙️ **現在の設定 - #{message.channel.name}**

**AI設定:**
🔹 プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`
🔹 最大トークン: `{self.ai_config.max_tokens if self.ai_config.max_tokens else '制限なし'}`

**システム設定:**
{current_setting[:500] + '...' if current_setting and len(current_setting) > 500 else current_setting or 'デフォルト設定'}"""
        
        await safe_send_message(message.channel, show_text)
    
    async def _handle_stats_command(self, message):
        """統計コマンドの処理"""
        channel_id = message.channel.id
        stats = self.conversation_manager.get_conversation_stats(channel_id)
        
        stats_text = f"""📊 **会話統計 - #{message.channel.name}**

💬 総メッセージ数: `{stats['total_messages']}件`
👤 ユーザーメッセージ: `{stats['user_messages']}件`
🤖 AIメッセージ: `{stats['assistant_messages']}件`
⚙️ システムメッセージ: `{stats['system_messages']}件`

**設定情報:**
🔹 AI プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`"""
        
        await safe_send_message(message.channel, stats_text)
    
    async def _handle_help_command(self, message):
        """ヘルプコマンドの処理"""
        help_text = f"""🤖 **{self.bot.user.name} の使用方法**

**AIと対話:**
📝 `/gpt [メッセージ]` または `/ai [メッセージ]`
例: `/gpt こんにちは！`

**設定・管理:**
🔄 `/reset` - 会話履歴をリセット
⚙️ `/setting` - プロンプト設定を管理
📊 `/stats` - 会話統計を表示
👁️ `/show` - 現在の設定を表示
❓ `/help` - このヘルプを表示

**プロンプト設定コマンド:**
📝 `/setting edit` - プロンプトを編集
👁️ `/setting show` - 現在のプロンプトを表示
💾 `/setting save [プロンプト]` - プロンプトを保存
🔄 `/setting reset` - デフォルト設定に戻す

**現在の設定:**
🔹 AI プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`

お気軽にお話しください！"""
        
        await safe_send_message(message.channel, help_text)
    
    async def _handle_ai_command(self, message):
        """AI対話コマンドの処理"""
        channel = message.channel
        channel_id = channel.id
        
        # コマンド部分を除去
        command = '/gpt' if message.content.startswith('/gpt') else '/ai'
        user_input = extract_command_content(message.content, command)
        
        if not user_input.strip():
            await safe_send_message(channel, "メッセージを入力してください。例: `/gpt こんにちは`")
            return
        
        # ログ出力
        logger.info(f"User: {message.author} ({message.author.id}) | Content: {user_input}")
        
        # 初回の場合はシステム設定を追加
        if not self.conversation_manager.get_messages(channel_id):
            current_setting = self.conversation_manager.get_system_setting(channel_id)
            if not current_setting:
                # チャンネル固有の設定があればそれを使用、なければデフォルト設定
                channel_prompt = get_channel_prompt(channel_id, self.prompt_config)
                self.conversation_manager.set_system_setting(channel_id, channel_prompt)
        
        # ユーザーメッセージを履歴に追加
        self.conversation_manager.add_message(channel_id, "user", user_input)
        
        try:
            # タイピング表示
            async with channel.typing():
                # AI応答生成
                messages = self.conversation_manager.get_messages(channel_id)
                ai_response = await self.ai_client.generate_response(messages)
            
            # 応答を履歴に追加
            self.conversation_manager.add_message(channel_id, "assistant", ai_response)
            
            # 応答を整形して送信
            formatted_response = format_response_text(ai_response)
            await safe_send_message(channel, formatted_response)
            
            logger.info(f"AI Response: {ai_response[:100]}...")
            
        except Exception as e:
            logger.error(f"AI API error: {e}", exc_info=True)
            
            # エラーの種類に応じたメッセージを表示
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                error_msg = f"AI サーバーへの接続に失敗しました。\nプロバイダー: {self.ai_config.provider}\nエラー: {str(e)}"
            else:
                error_msg = f"AI API でエラーが発生しました。\nプロバイダー: {self.ai_config.provider}\nエラー: {str(e)}"
            
            await safe_send_message(channel, error_msg)
            
            # エラー時は最後のユーザーメッセージを削除
            messages = self.conversation_manager.get_messages(channel_id)
            if messages and messages[-1]["role"] == "user":
                messages.pop()
    
    async def _send_login_message(self):
        """登録チャンネルにログインメッセージを送信"""
        if not self.discord_config.channel_ids:
            logger.info("チャンネル制限なし - ログインメッセージは送信しません")
            return
        
        login_message = f"""🤖 **{self.bot.user.name} がログインしました！**

**AI設定情報:**
🔹 プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`

**利用可能なコマンド:**
📝 `/gpt [メッセージ]` または `/ai [メッセージ]` - AIと対話
🔄 `/reset` - 会話履歴をリセット
⚙️ `/setting` - プロンプト設定を管理
📊 `/stats` - 会話統計を表示
👁️ `/show` - 現在の設定を表示
❓ `/help` - ヘルプを表示

準備完了です！お気軽にお話しください。"""

        successful_channels = []
        failed_channels = []
        
        for channel_id in self.discord_config.channel_ids:
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    await safe_send_message(channel, login_message)
                    successful_channels.append(f"#{channel.name} ({channel_id})")
                    logger.info(f"ログインメッセージを送信しました: #{channel.name} ({channel_id})")
                else:
                    failed_channels.append(f"チャンネルが見つかりません: {channel_id}")
                    logger.warning(f"チャンネルが見つかりません: {channel_id}")
            except Exception as e:
                failed_channels.append(f"{channel_id}: {str(e)}")
                logger.error(f"ログインメッセージ送信エラー (チャンネル {channel_id}): {e}")
        
        # 結果をログに出力
        if successful_channels:
            logger.info(f"ログインメッセージ送信成功: {', '.join(successful_channels)}")
        if failed_channels:
            logger.warning(f"ログインメッセージ送信失敗: {', '.join(failed_channels)}")
    
    async def _handle_setting_command(self, message):
        """設定プロンプトコマンドの処理"""
        channel = message.channel
        channel_id = channel.id
        content = message.content.strip()
        
        # コマンドの引数を解析
        parts = content.split(' ', 1)
        
        if len(parts) == 1:
            # `/setting` のみの場合：現在の設定を表示
            current_prompt = get_channel_prompt(channel_id, self.prompt_config)
            is_custom = str(channel_id) in self.prompt_config.settings
            
            setting_text = f"""⚙️ **プロンプト設定 - #{channel.name}**

**現在の設定:**
{"🔧 カスタム設定" if is_custom else "📋 デフォルト設定"}

**利用可能なコマンド:**
📝 `/setting edit` - プロンプトを編集
👁️ `/setting show` - 現在のプロンプトを全文表示
🔄 `/setting reset` - デフォルト設定に戻す
💾 `/setting save [プロンプト]` - 新しいプロンプトを保存

例: `/setting save あなたは優しいアシスタントです。`"""
            
            await safe_send_message(channel, setting_text)
            return
        
        subcommand = parts[1].strip()
        
        if subcommand == "show":
            # 現在のプロンプトを全文表示
            current_prompt = get_channel_prompt(channel_id, self.prompt_config)
            is_custom = str(channel_id) in self.prompt_config.settings
            
            show_text = f"""📋 **現在のプロンプト設定 - #{channel.name}**

**タイプ:** {"🔧 カスタム設定" if is_custom else "📋 デフォルト設定"}

**プロンプト内容:**
```
{current_prompt}
```"""
            
            # Discordのメッセージ長制限（2000文字）を考慮
            if len(show_text) > 1900:
                show_text = show_text[:1900] + "...\n```\n*（プロンプトが長いため省略されました）*"
            
            await safe_send_message(channel, show_text)
            
        elif subcommand == "edit":
            # プロンプト編集モード
            current_prompt = get_channel_prompt(channel_id, self.prompt_config)
            
            edit_text = f"""✏️ **プロンプト編集モード - #{channel.name}**

**現在のプロンプト:**
```
{current_prompt[:500] + '...' if len(current_prompt) > 500 else current_prompt}
```

新しいプロンプトを入力してください（5分以内）。
キャンセルする場合は `/cancel` を入力してください。"""
            
            await safe_send_message(channel, edit_text)
            
            def check(m):
                return m.author == message.author and m.channel == channel
            
            try:
                response = await self.bot.wait_for('message', check=check, timeout=300.0)
                
                if response.content.strip() == "/cancel":
                    await safe_send_message(channel, "プロンプト編集をキャンセルしました。")
                    return
                
                new_prompt = response.content.strip()
                if not new_prompt:
                    await safe_send_message(channel, "プロンプトが空です。編集をキャンセルしました。")
                    return
                
                # プロンプトを保存
                set_channel_prompt(channel_id, new_prompt, self.prompt_config)
                
                # 現在の会話をリセット
                self.conversation_manager.reset_conversation(channel_id, new_prompt)
                
                await safe_send_message(channel, "✅ プロンプトを更新し、会話をリセットしました。")
                logger.info(f"Channel {channel_id}: Custom prompt updated")
                
            except asyncio.TimeoutError:
                await safe_send_message(channel, "⏰ タイムアウトしました。プロンプト編集をキャンセルします。")
        
        elif subcommand.startswith("save "):
            # 直接プロンプトを保存
            new_prompt = subcommand[5:].strip()  # "save " を除去
            
            if not new_prompt:
                await safe_send_message(channel, "プロンプトが空です。例: `/setting save あなたは優しいアシスタントです。`")
                return
            
            # プロンプトを保存
            set_channel_prompt(channel_id, new_prompt, self.prompt_config)
            
            # 現在の会話をリセット
            self.conversation_manager.reset_conversation(channel_id, new_prompt)
            
            await safe_send_message(channel, "✅ プロンプトを保存し、会話をリセットしました。")
            logger.info(f"Channel {channel_id}: Custom prompt saved")
        
        elif subcommand == "reset":
            # デフォルト設定に戻す
            delete_channel_prompt(channel_id, self.prompt_config)
            
            # 会話をデフォルト設定でリセット
            self.conversation_manager.reset_conversation(channel_id, DEFAULT_SETTING)
            
            await safe_send_message(channel, "✅ プロンプトをデフォルト設定に戻し、会話をリセットしました。")
            logger.info(f"Channel {channel_id}: Prompt reset to default")
        
        else:
            await safe_send_message(channel, """❌ 不明なサブコマンドです。

**利用可能なコマンド:**
📝 `/setting edit` - プロンプトを編集
👁️ `/setting show` - 現在のプロンプトを全文表示
🔄 `/setting reset` - デフォルト設定に戻す
💾 `/setting save [プロンプト]` - 新しいプロンプトを保存""")

    # ...existing code...
    
def run(self):
        """ボットを実行"""
        if not self.discord_config.token:
            logger.error("Discord token is not set. Please set DISCORD_TOKEN environment variable.")
            return
        
        try:
            self.bot.run(self.discord_config.token)
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot error: {e}")

def main():
    """メイン関数"""
    bot = ChatBot()
    bot.run()

if __name__ == "__main__":
    main()