"""
Discord AI Bot
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
from voice_handler import VoiceHandler

# 環境変数を読み込み
load_dotenv()

# ログ設定
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))

class ChatBot:
    """メインのボットクラス"""
    
    def __init__(self):
        # 設定読み込み
        self.ai_config, self.discord_config, self.prompt_config = load_config()
        
        # DMチャンネルの許可設定
        self.allow_dm = True
        
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
        
        # 音声ハンドラー初期化
        self.voice_handler = VoiceHandler()
        
        # Discord Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True  # ギルド情報の取得に必要
        
        # Bot初期化時にコマンドの自動同期を有効化
        self.bot = commands.Bot(
            command_prefix='/', 
            intents=intents,
            sync_commands=True,  # コマンドの自動同期
            sync_commands_debug=True,  # デバッグ情報の出力
            application_id=int(os.getenv("BOT_APPLICATION_ID", "0"))  # アプリケーションID
        )
        
        # イベントハンドラー登録
        self._setup_events()
        
        # スラッシュコマンド登録
        self._setup_slash_commands()
        logger.info("スラッシュコマンドを設定しました")
        logger.info(f"登録されたコマンド数: {len(self.bot.tree.get_commands())}")
        for cmd in self.bot.tree.get_commands():
            logger.info(f"  - /{cmd.name}: {cmd.description}")
        
        logger.info(f"Bot initialized with AI provider: {self.ai_config.provider}")
    
    def _check_channel_permission(self, interaction: discord.Interaction) -> bool:
        """
        チャンネル権限を確認するヘルパーメソッド
        
        Args:
            interaction (discord.Interaction): インタラクション
        
        Returns:
            bool: チャンネルで許可されているかどうか
        """
        # DMチャンネルかどうか確認
        is_dm = interaction.guild is None
        
        # DMチャンネル許可設定に基づいて確認
        return validate_channel_access(
            interaction.channel_id,
            self.discord_config.channel_ids,
            is_dm=(is_dm and self.allow_dm)
        )
    
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
            
            # スラッシュコマンドを同期
            try:
                logger.info("スラッシュコマンドの同期を開始...")
                
                # グローバル同期（全サーバー対応）
                synced = await self.bot.tree.sync()
                logger.info(f"グローバルスラッシュコマンドを同期しました: {len(synced)}個のコマンド")
                
                # 同期されたコマンドのリストを表示
                for command in synced:
                    logger.info(f"  - /{command.name}: {command.description}")
                
                # 開発用：特定のギルドで即座に同期（本番では削除推奨）
                if os.getenv("DEV_GUILD_ID"):
                    dev_guild_id = int(os.getenv("DEV_GUILD_ID"))
                    guild = discord.Object(id=dev_guild_id)
                    try:
                        dev_synced = await self.bot.tree.sync(guild=guild)
                        logger.info(f"開発ギルドでコマンド同期: {len(dev_synced)}個")
                    except Exception as e:
                        logger.error(f"開発ギルド同期エラー: {e}")
                
            except Exception as e:
                logger.error(f"スラッシュコマンドの同期に失敗しました: {e}", exc_info=True)
                # 詳細なエラー情報を表示
                if hasattr(e, 'response'):
                    logger.error(f"HTTP Status: {e.response.status}")
                    logger.error(f"Response: {await e.response.text()}")
            
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
            
            # チャンネル権限確認（DMは常に許可）
            is_dm = message.guild is None
            if not validate_channel_access(message.channel.id, self.discord_config.channel_ids, is_dm=(is_dm and self.allow_dm)):
                return
            
            # コマンド処理を行う
            await self.bot.process_commands(message)
    
    def _setup_slash_commands(self):
        """スラッシュコマンドを設定"""
        
        @self.bot.tree.command(name="gpt", description="AIと対話します")
        async def gpt_command(interaction: discord.Interaction, prompt: str):
            """AIと対話するスラッシュコマンド"""
            # チャンネル権限確認
            if not self._check_channel_permission(interaction):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_ai_slash_command(interaction, prompt)
        
        @self.bot.tree.command(name="ai", description="AIと対話します（gptコマンドと同じ）")
        async def ai_command(interaction: discord.Interaction, prompt: str):
            """AIと対話するスラッシュコマンド（エイリアス）"""
            # チャンネル権限確認
            if not self._check_channel_permission(interaction):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_ai_slash_command(interaction, prompt)
        
        @self.bot.tree.command(name="reset", description="会話履歴をリセットします")
        async def reset_command(interaction: discord.Interaction):
            """会話リセットのスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_reset_slash_command(interaction)
        
        @self.bot.tree.command(name="show", description="現在の設定を表示します")
        async def show_command(interaction: discord.Interaction):
            """設定表示のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_show_slash_command(interaction)
        
        @self.bot.tree.command(name="stats", description="会話統計を表示します")
        async def stats_command(interaction: discord.Interaction):
            """統計表示のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_stats_slash_command(interaction)
        
        @self.bot.tree.command(name="help", description="ヘルプを表示します")
        async def help_command(interaction: discord.Interaction):
            """ヘルプ表示のスラッシュコマンド"""
            await self._handle_help_slash_command(interaction)
        
        # プロンプト設定用のグループコマンド
        setting_group = discord.app_commands.Group(name="setting", description="プロンプト設定を管理します")
        
        @setting_group.command(name="show", description="現在のプロンプト設定を表示します")
        async def setting_show_command(interaction: discord.Interaction):
            """プロンプト設定表示のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_setting_show_slash_command(interaction)
        
        @setting_group.command(name="save", description="新しいプロンプトを保存します")
        async def setting_save_command(interaction: discord.Interaction, prompt: str):
            """プロンプト保存のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_setting_save_slash_command(interaction, prompt)
        
        @setting_group.command(name="reset", description="プロンプトをデフォルト設定に戻します")
        async def setting_reset_command(interaction: discord.Interaction):
            """プロンプトリセットのスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_setting_reset_slash_command(interaction)
        
        @setting_group.command(name="edit", description="プロンプトを対話的に編集します")
        async def setting_edit_command(interaction: discord.Interaction):
            """プロンプト編集のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_setting_edit_slash_command(interaction)
        
        # グループコマンドをツリーに追加
        self.bot.tree.add_command(setting_group)
        
        # 音声関連のコマンド
        @self.bot.tree.command(name="tel", description="ボイスチャンネルでAIと対話します")
        async def tel_command(interaction: discord.Interaction):
            """ボイスチャンネルでAIと対話するコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_tel_slash_command(interaction)
        
        # 音声設定用のグループコマンド
        voice_setting_group = discord.app_commands.Group(name="voice_setting", description="音声設定を管理します")
        
        @voice_setting_group.command(name="list", description="利用可能な音声タイプの一覧を表示します")
        async def voice_setting_list_command(interaction: discord.Interaction):
            """音声タイプ一覧表示のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_voice_setting_list_slash_command(interaction)
        
        @voice_setting_group.command(name="user_default", description="ユーザーのデフォルト音声タイプを設定します")
        @discord.app_commands.describe(voice_type="音声タイプ")
        async def voice_setting_user_default_command(interaction: discord.Interaction, voice_type: str):
            """ユーザーのデフォルト音声タイプ設定のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_voice_setting_user_default_slash_command(interaction, voice_type)
        
        @voice_setting_group.command(name="channel_default", description="チャンネルのデフォルト音声タイプを設定します")
        @discord.app_commands.describe(voice_type="音声タイプ")
        async def voice_setting_channel_default_command(interaction: discord.Interaction, voice_type: str):
            """チャンネルのデフォルト音声タイプ設定のスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_voice_setting_channel_default_slash_command(interaction, voice_type)
        
        # グループコマンドをツリーに追加
        self.bot.tree.add_command(voice_setting_group)
        
        @self.bot.tree.command(name="tts", description="入力したテキストをそのまま音声に変換して送信します")
        @discord.app_commands.describe(
            text="音声に変換するテキスト",
            voice_type="音声タイプ (未指定の場合はユーザーまたはチャンネルのデフォルト設定を使用)"
        )
        async def tts_command(
            interaction: discord.Interaction, 
            text: str, 
            voice_type: str = None
        ):
            """入力テキストをそのまま音声に変換して送信するコマンド"""
            # チャンネル権限確認
            if not self._check_channel_permission(interaction):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_tts_slash_command(interaction, text, voice_type)
        
        @self.bot.tree.command(name="voice", description="入力に対するAIの返答を生成し、その返答を音声で送信します")
        @discord.app_commands.describe(
            text="AIへの質問や指示",
            voice_type="音声タイプ (未指定の場合はユーザーまたはチャンネルのデフォルト設定を使用)"
        )
        async def voice_command(
            interaction: discord.Interaction, 
            text: str, 
            voice_type: str = None
        ):
            """AIの返答を音声に変換して送信するコマンド"""
            # チャンネル権限確認
            if not self._check_channel_permission(interaction):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_voice_slash_command(interaction, text, voice_type)
    
    async def _handle_ai_slash_command(self, interaction: discord.Interaction, prompt: str):
        """AI対話スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        
        # ログ出力
        logger.info(f"User: {interaction.user} ({interaction.user.id}) | Content: {prompt}")
        
        # 初回の場合はシステム設定を追加
        if not self.conversation_manager.get_messages(channel_id):
            current_setting = self.conversation_manager.get_system_setting(channel_id)
            if not current_setting:
                # チャンネル固有の設定があればそれを使用、なければデフォルト設定
                channel_prompt = get_channel_prompt(channel_id, self.prompt_config)
                self.conversation_manager.set_system_setting(channel_id, channel_prompt)
        
        # ユーザーメッセージを履歴に追加
        self.conversation_manager.add_message(channel_id, "user", prompt)
        
        try:
            # 応答を遅延させる（処理時間が長い場合）
            await interaction.response.defer()
            
            # AI応答生成
            messages = self.conversation_manager.get_messages(channel_id)
            ai_response = await self.ai_client.generate_response(messages)
            
            # 応答を履歴に追加
            self.conversation_manager.add_message(channel_id, "assistant", ai_response)
            
            # 応答を整形して送信
            formatted_response = format_response_text(ai_response)
            await interaction.followup.send(formatted_response)
            
            logger.info(f"AI Response: {ai_response[:100]}...")
            
        except Exception as e:
            logger.error(f"AI API error: {e}", exc_info=True)
            
            # エラーの種類に応じたメッセージを表示
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                error_msg = f"AI サーバーへの接続に失敗しました。\nプロバイダー: {self.ai_config.provider}\nエラー: {str(e)}"
            else:
                error_msg = f"AI API でエラーが発生しました。\nプロバイダー: {self.ai_config.provider}\nエラー: {str(e)}"
            
            if interaction.response.is_done():
                await interaction.followup.send(error_msg)
            else:
                await interaction.response.send_message(error_msg)
            
            # エラー時は最後のユーザーメッセージを削除
            messages = self.conversation_manager.get_messages(channel_id)
            if messages and messages[-1]["role"] == "user":
                messages.pop()
    
    async def _handle_reset_slash_command(self, interaction: discord.Interaction):
        """リセットスラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        
        # チャンネル固有の設定があればそれを使用、なければデフォルト設定
        new_setting = get_channel_prompt(channel_id, self.prompt_config)
        self.conversation_manager.reset_conversation(channel_id, new_setting)
        
        await interaction.response.send_message("✅ 会話履歴をリセットしました。")
        logger.info(f"Channel {channel_id}: Conversation reset")
    
    async def _handle_show_slash_command(self, interaction: discord.Interaction):
        """設定表示スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        current_setting = self.conversation_manager.get_system_setting(channel_id)
        
        show_text = f"""⚙️ **現在の設定 - <#{channel_id}>**

**AI設定:**
🔹 プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`
🔹 最大トークン: `{self.ai_config.max_tokens if self.ai_config.max_tokens else '制限なし'}`

**システム設定:**
{current_setting[:500] + '...' if current_setting and len(current_setting) > 500 else current_setting or 'デフォルト設定'}"""
        
        await interaction.response.send_message(show_text)
    
    async def _handle_stats_slash_command(self, interaction: discord.Interaction):
        """統計スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        stats = self.conversation_manager.get_conversation_stats(channel_id)
        
        stats_text = f"""📊 **会話統計 - <#{channel_id}>**

💬 総メッセージ数: `{stats['total_messages']}件`
👤 ユーザーメッセージ: `{stats['user_messages']}件`
🤖 AIメッセージ: `{stats['assistant_messages']}件`
⚙️ システムメッセージ: `{stats['system_messages']}件`

**設定情報:**
🔹 AI プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`"""
        
        await interaction.response.send_message(stats_text)
    
    async def _handle_help_slash_command(self, interaction: discord.Interaction):
        """ヘルプスラッシュコマンドの処理"""
        help_text = f"""🤖 **{self.bot.user.name} の使用方法**

**AIと対話:**
📝 `/gpt [prompt]` または `/ai [prompt]` - AIと対話
例: `/gpt こんにちは！`

**設定・管理:**
🔄 `/reset` - 会話履歴をリセット
📊 `/stats` - 会話統計を表示
👁️ `/show` - 現在の設定を表示
❓ `/help` - このヘルプを表示

**プロンプト設定コマンド:**
📝 `/setting edit` - プロンプトを対話的に編集
👁️ `/setting show` - 現在のプロンプトを表示
💾 `/setting save [prompt]` - プロンプトを保存
🔄 `/setting reset` - デフォルト設定に戻す

**音声機能:**
🎤 `/tel` - ボイスチャンネルでAIと対話
🔊 `/tts [text]` - 入力したテキストをそのまま音声に変換して送信
🤖 `/voice [text]` - 入力に対するAI返答を生成し、音声で送信
🔧 `/voice_setting list` - 利用可能な音声タイプを表示
👤 `/voice_setting user_default [type]` - あなたのデフォルト音声タイプを設定
📢 `/voice_setting channel_default [type]` - チャンネルのデフォルト音声タイプを設定

**現在の設定:**
🔹 AI プロバイダー: `{self.ai_config.provider.upper()}`
🔹 モデル: `{self.ai_config.ollama_model if self.ai_config.provider == 'ollama' else self.ai_config.openai_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`

お気軽にお話しください！"""
        
        await interaction.response.send_message(help_text)
    
    async def _handle_setting_show_slash_command(self, interaction: discord.Interaction):
        """プロンプト設定表示スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        current_prompt = get_channel_prompt(channel_id, self.prompt_config)
        is_custom = str(channel_id) in self.prompt_config.settings
        
        show_text = f"""📋 **現在のプロンプト設定 - <#{channel_id}>**

**タイプ:** {"🔧 カスタム設定" if is_custom else "📋 デフォルト設定"}

**プロンプト内容:**
```
{current_prompt}
```"""
        
        # Discordのメッセージ長制限（2000文字）を考慮
        if len(show_text) > 1900:
            show_text = show_text[:1900] + "...\n```\n*（プロンプトが長いため省略されました）*"
        
        await interaction.response.send_message(show_text)
    
    async def _handle_setting_save_slash_command(self, interaction: discord.Interaction, prompt: str):
        """プロンプト保存スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        
        if not prompt.strip():
            await interaction.response.send_message("プロンプトが空です。", ephemeral=True)
            return
        
        # プロンプトを保存
        set_channel_prompt(channel_id, prompt, self.prompt_config)
        
        # 現在の会話をリセット
        self.conversation_manager.reset_conversation(channel_id, prompt)
        
        await interaction.response.send_message("✅ プロンプトを保存し、会話をリセットしました。")
        logger.info(f"Channel {channel_id}: Custom prompt saved")
    
    async def _handle_setting_reset_slash_command(self, interaction: discord.Interaction):
        """プロンプトリセットスラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        
        # デフォルト設定に戻す
        delete_channel_prompt(channel_id, self.prompt_config)
        
        # 会話をデフォルト設定でリセット
        self.conversation_manager.reset_conversation(channel_id, DEFAULT_SETTING)
        
        await interaction.response.send_message("✅ プロンプトをデフォルト設定に戻し、会話をリセットしました。")
        logger.info(f"Channel {channel_id}: Prompt reset to default")
    
    async def _handle_setting_edit_slash_command(self, interaction: discord.Interaction):
        """プロンプト編集スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        current_prompt = get_channel_prompt(channel_id, self.prompt_config)
        
        edit_text = f"""✏️ **プロンプト編集モード - <#{channel_id}>**

**現在のプロンプト:**
```
{current_prompt[:500] + '...' if len(current_prompt) > 500 else current_prompt}
```

新しいプロンプトを入力してください（5分以内）。
キャンセルする場合は `cancel` を入力してください。"""
        
        await interaction.response.send_message(edit_text)
        
        def check(m):
            return m.author == interaction.user and m.channel.id == channel_id
        
        try:
            response = await self.bot.wait_for('message', check=check, timeout=300.0)
            
            if response.content.strip().lower() == "cancel":
                await response.reply("プロンプト編集をキャンセルしました。")
                return
            
            new_prompt = response.content.strip()
            if not new_prompt:
                await response.reply("プロンプトが空です。編集をキャンセルしました。")
                return
            
            # プロンプトを保存
            set_channel_prompt(channel_id, new_prompt, self.prompt_config)
            
            # 現在の会話をリセット
            self.conversation_manager.reset_conversation(channel_id, new_prompt)
            
            await response.reply("✅ プロンプトを更新し、会話をリセットしました。")
            logger.info(f"Channel {channel_id}: Custom prompt updated")
            
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ タイムアウトしました。プロンプト編集をキャンセルします。")
    
    async def _handle_tel_slash_command(self, interaction: discord.Interaction):
        """ボイスチャンネルでAIと対話するコマンドの処理"""
        # ユーザーがボイスチャンネルに接続しているか確認
        if not interaction.user.voice:
            await interaction.response.send_message("ボイスチャンネルに接続してから実行してください。", ephemeral=True)
            return

        voice_channel = interaction.user.voice.channel

        # 応答を遅延させる（処理時間が長い場合）
        await interaction.response.defer()

        # ボイスチャンネルに接続
        success = await self.voice_handler.join_voice_channel(voice_channel)
        if not success:
            await interaction.followup.send("ボイスチャンネルへの接続に失敗しました。")
            return

        await interaction.followup.send(
            f"{voice_channel.name}に接続して音声対話を開始します。\n"
            "5秒間録音します。録音後、ファイルパスをログに出力します。"
        )

        logger.info(f"ボイス対話コマンド実行: {interaction.user.name}, チャンネル: {voice_channel.name}")

        # 5秒間録音し、ファイルパスをログ出力
        audio_path = await self.voice_handler.record_audio(voice_channel.guild.id, duration=5.0, user_id=interaction.user.id)
        if audio_path:
            logger.info(f"録音ファイル: {audio_path}")
        else:
            logger.warning("録音に失敗しました")
    
    async def _handle_tts_slash_command(self, interaction: discord.Interaction, text: str, voice_type: str = None):
        """入力テキストをそのまま音声に変換して送信するコマンドの処理"""
        await interaction.response.defer()
        
        logger.info(f"TTS実行: {interaction.user.name}, テキスト: {text}, 音声タイプ: {voice_type}")
        
        try:
            # TTSエンドポイントを使用して音声合成
            synthesized_audio = await self.voice_handler.synthesize_speech(
                text=text,
                media_type='wav',
                voice_preset=voice_type,
                user_id=interaction.user.id,
                channel_id=interaction.channel_id
            )
            
            if synthesized_audio:
                # 音声ファイルが生成できた場合、添付ファイルとして送信
                await interaction.followup.send(
                    f"生成された音声ファイルです：\n「{text}」", 
                    file=discord.File(synthesized_audio, filename=f"tts_{interaction.user.id}.wav")
                )
                
                # ユーザーがボイスチャンネルに接続している場合は、そこでも再生
                if interaction.user.voice:
                    voice_channel = interaction.user.voice.channel
                    # ボイスチャンネルに接続
                    success = await self.voice_handler.join_voice_channel(voice_channel)
                    if success:
                        # 音声を再生
                        await self.voice_handler.play_audio(voice_channel.guild.id, synthesized_audio)
            else:
                await interaction.followup.send(
                    f"音声生成に失敗しました。TTSサーバー（http://127.0.0.1:9880）が起動しているか確認してください。\n"
                    f"入力テキスト: {text}"
                )
        except Exception as e:
            logger.error(f"TTS実行エラー: {e}", exc_info=True)
            await interaction.followup.send(f"音声生成中にエラーが発生しました: {e}")
    
    async def _handle_voice_slash_command(self, interaction: discord.Interaction, text: str, voice_type: str = None):
        """AIの返答を音声に変換して送信するコマンドの処理"""
        await interaction.response.defer()
        
        logger.info(f"AI音声生成コマンド実行: {interaction.user.name}, テキスト: {text}, 音声タイプ: {voice_type}")
        
        try:
            # チャンネルIDを取得
            channel_id = interaction.channel_id
            
            # 初回の場合はシステム設定を追加
            if not self.conversation_manager.get_messages(channel_id):
                current_setting = self.conversation_manager.get_system_setting(channel_id)
                if not current_setting:
                    # チャンネル固有の設定があればそれを使用、なければデフォルト設定
                    channel_prompt = get_channel_prompt(channel_id, self.prompt_config)
                    self.conversation_manager.set_system_setting(channel_id, channel_prompt)
            
            # ユーザーメッセージを履歴に追加
            self.conversation_manager.add_message(channel_id, "user", text)
            
            # AI応答生成
            messages = self.conversation_manager.get_messages(channel_id)
            ai_response = await self.ai_client.generate_response(messages)
            
            # 応答を履歴に追加
            self.conversation_manager.add_message(channel_id, "assistant", ai_response)
            
            # 応答を整形
            formatted_response = format_response_text(ai_response)
            
            # メッセージでAI応答を送信
            await interaction.followup.send(f"🤖 AIの回答: \n{formatted_response}")
            
            # 音声合成で応答を読み上げる
            synthesized_audio = await self.voice_handler.synthesize_speech(
                text=ai_response,
                media_type='wav',
                voice_preset=voice_type,
                user_id=interaction.user.id,
                channel_id=interaction.channel_id
            )
            
            if synthesized_audio:
                # 音声ファイルが生成できた場合、添付ファイルとして送信
                await interaction.followup.send(
                    f"AIの回答を音声で聞く:", 
                    file=discord.File(synthesized_audio, filename=f"ai_voice_{interaction.user.id}.wav")
                )
                
                # ユーザーがボイスチャンネルに接続している場合は、そこでも再生
                if interaction.user.voice:
                    voice_channel = interaction.user.voice.channel
                    # ボイスチャンネルに接続
                    success = await self.voice_handler.join_voice_channel(voice_channel)
                    if success:
                        # 音声を再生
                        await self.voice_handler.play_audio(voice_channel.guild.id, synthesized_audio)
            else:
                await interaction.followup.send(
                    f"AI応答の音声生成に失敗しました。TTSサーバー（http://127.0.0.1:9880）が起動しているか確認してください。"
                )
                
        except Exception as e:
            logger.error(f"AI音声生成エラー: {e}", exc_info=True)
            await interaction.followup.send(f"AI応答または音声生成中にエラーが発生しました: {e}")
    
    async def _handle_voice_setting_list_slash_command(self, interaction: discord.Interaction):
        """音声タイプ一覧表示コマンドの処理"""
        # 音声プリセット一覧を取得
        presets = self.voice_handler.settings.get_all_presets()
        
        # ユーザーとチャンネルのデフォルト設定を取得
        user_default = self.voice_handler.settings.get_user_default(interaction.user.id)
        channel_default = self.voice_handler.settings.get_channel_default(interaction.channel_id)
        
        # 一覧を整形して表示
        preset_list = "\n".join([
            f"📌 `{preset_id}`: {preset_data.get('name', preset_id)}" +
            (" 👤" if preset_id == user_default else "") +
            (" 📢" if preset_id == channel_default else "")
            for preset_id, preset_data in presets.items()
        ])
        
        message = f"""🔊 **利用可能な音声タイプ一覧**

{preset_list}

**現在の設定:**
👤 あなたのデフォルト: `{user_default}`（{presets[user_default].get('name', user_default)}）
📢 このチャンネルのデフォルト: `{channel_default}`（{presets[channel_default].get('name', channel_default)}）

**設定変更コマンド:**
- `/voice_setting user_default [voice_type]` - あなたのデフォルト設定を変更
- `/voice_setting channel_default [voice_type]` - このチャンネルのデフォルト設定を変更

**使い方:**
- `/voice [text]` - デフォルト音声でテキストを読み上げ
- `/voice [text] voice_type:[type]` - 指定した音声タイプでテキストを読み上げ

👤：ユーザーデフォルト設定
📢：チャンネルデフォルト設定"""
        
        await interaction.response.send_message(message)
    
    async def _handle_voice_setting_user_default_slash_command(self, interaction: discord.Interaction, voice_type: str):
        """ユーザーのデフォルト音声タイプ設定コマンドの処理"""
        # 存在する音声タイプか確認
        presets = self.voice_handler.settings.get_all_presets()
        if voice_type not in presets:
            preset_list = ", ".join([f"`{p_id}`" for p_id in presets.keys()])
            await interaction.response.send_message(
                f"❌ 指定された音声タイプ `{voice_type}` は存在しません。\n"
                f"利用可能な音声タイプ: {preset_list}\n"
                f"利用可能な音声タイプの詳細は `/voice_setting list` で確認できます。",
                ephemeral=True
            )
            return
        
        # 音声タイプを設定
        success = self.voice_handler.settings.set_user_default(interaction.user.id, voice_type)
        if success:
            preset_name = presets[voice_type].get('name', voice_type)
            await interaction.response.send_message(
                f"✅ あなたのデフォルト音声タイプを `{voice_type}` ({preset_name}) に設定しました。\n"
                f"今後、`/voice` コマンドで音声タイプを指定しない場合はこの設定が使用されます。"
            )
        else:
            await interaction.response.send_message(
                f"❌ デフォルト音声タイプの設定に失敗しました。",
                ephemeral=True
            )
    
    async def _handle_voice_setting_channel_default_slash_command(self, interaction: discord.Interaction, voice_type: str):
        """チャンネルのデフォルト音声タイプ設定コマンドの処理"""
        # ユーザーが管理者権限を持っているか確認
        if not interaction.permissions.administrator:
            await interaction.response.send_message(
                "❌ このコマンドを実行するには管理者権限が必要です。",
                ephemeral=True
            )
            return
            
        # 存在する音声タイプか確認
        presets = self.voice_handler.settings.get_all_presets()
        if voice_type not in presets:
            preset_list = ", ".join([f"`{p_id}`" for p_id in presets.keys()])
            await interaction.response.send_message(
                f"❌ 指定された音声タイプ `{voice_type}` は存在しません。\n"
                f"利用可能な音声タイプ: {preset_list}\n"
                f"利用可能な音声タイプの詳細は `/voice_setting list` で確認できます。",
                ephemeral=True
            )
            return
        
        # 音声タイプを設定
        success = self.voice_handler.settings.set_channel_default(interaction.channel_id, voice_type)
        if success:
            preset_name = presets[voice_type].get('name', voice_type)
            await interaction.response.send_message(
                f"✅ このチャンネルのデフォルト音声タイプを `{voice_type}` ({preset_name}) に設定しました。\n"
                f"今後、このチャンネルで `/voice` コマンドで音声タイプを指定しない場合、かつユーザーのデフォルト設定がない場合はこの設定が使用されます。"
            )
        else:
            await interaction.response.send_message(
                f"❌ デフォルト音声タイプの設定に失敗しました。",
                ephemeral=True
            )
    
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

**利用可能なスラッシュコマンド:**
📝 `/gpt [prompt]` または `/ai [prompt]` - AIと対話
🔄 `/reset` - 会話履歴をリセット
⚙️ `/setting` グループ - プロンプト設定を管理
📊 `/stats` - 会話統計を表示
👁️ `/show` - 現在の設定を表示
❓ `/help` - ヘルプを表示
🎤 `/tel` - ボイスチャンネルでAIと対話
🔊 `/tts [text]` - テキストをそのまま音声に変換
🤖 `/voice [text]` - AI返答を生成し音声で送信

**プロンプト設定コマンド:**
📝 `/setting edit` - プロンプトを対話的に編集
👁️ `/setting show` - 現在のプロンプトを表示
💾 `/setting save [prompt]` - プロンプトを保存
🔄 `/setting reset` - デフォルト設定に戻す

準備完了です！チャット欄で `/` を入力するとコマンド一覧が表示されます。"""

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