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

from config import load_config, DEFAULT_SETTING
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
        self.ai_config, self.discord_config = load_config()
        
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
        
        @self.bot.event
        async def on_message(message):
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
            if message.content.startswith('/reset'):
                await self._handle_reset_command(message)
            elif message.content.startswith('/show'):
                await self._handle_show_command(message)
            elif message.content.startswith('/stats'):
                await self._handle_stats_command(message)
            elif message.content.startswith('/help'):
                await self._handle_help_command(message)
            elif message.content.startswith('/gpt') or message.content.startswith('/ai'):
                await self._handle_ai_command(message)
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
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
                new_setting = DEFAULT_SETTING
            else:
                new_setting = msg.content
            
            self.conversation_manager.reset_conversation(channel_id, new_setting)
            
            await safe_send_message(channel, "初期化を行いました。")
            logger.info(f"Channel {channel_id}: Conversation reset")
            
        except asyncio.TimeoutError:
            await safe_send_message(channel, "タイムアウトしました。リセットをキャンセルします。")
    
    async def _handle_show_command(self, message):
        """設定表示コマンドの処理"""
        channel = message.channel
        channel_id = channel.id
        
        current_setting = self.conversation_manager.get_system_setting(channel_id)
        if current_setting:
            setting_text = current_setting
        else:
            setting_text = DEFAULT_SETTING
        
        await safe_send_message(channel, '現在のAIの設定はこのようになっています。')
        await safe_send_message(channel, f"```\n{setting_text}\n```")
        await safe_send_message(channel, '設定を変更したい場合は `/reset` と入力してください。')
    
    async def _handle_stats_command(self, message):
        """統計表示コマンドの処理"""
        channel = message.channel
        channel_id = channel.id
        
        stats = self.conversation_manager.get_conversation_stats(channel_id)
        stats_text = f"""**会話統計**
総メッセージ数: {stats['total_messages']}
ユーザーメッセージ: {stats['user_messages']}
AIメッセージ: {stats['assistant_messages']}
システムメッセージ: {stats['system_messages']}
AI Provider: {self.ai_config.provider}"""
        
        await safe_send_message(channel, stats_text)
    
    async def _handle_help_command(self, message):
        """ヘルプコマンドの処理"""
        help_text = """**利用可能なコマンド**
`/gpt [メッセージ]` または `/ai [メッセージ]` - AIと対話
`/reset` - 会話履歴をリセットし、設定を変更
`/show` - 現在の設定を表示
`/stats` - 会話統計を表示
`/help` - このヘルプを表示

**設定情報**
AI Provider: {}
Model: {}""".format(
            self.ai_config.provider,
            self.ai_config.openai_model if self.ai_config.provider == "openai" else self.ai_config.ollama_model
        )
        
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
                self.conversation_manager.set_system_setting(channel_id, DEFAULT_SETTING)
        
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
            logger.error(f"AI API error: {e}")
            await safe_send_message(
                channel,
                f"申し訳ございません。AI APIでエラーが発生しました。\nエラー: {str(e)}"
            )
            
            # エラー時は最後のユーザーメッセージを削除
            messages = self.conversation_manager.get_messages(channel_id)
            if messages and messages[-1]["role"] == "user":
                messages.pop()
    
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