"""
Discord AI Bot
OpenAI API と Ollama API の両方に対応した Discord ボット
"""
import os
import sys
import asyncio
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import discord
from discord.ext import commands
from dotenv import load_dotenv
from collections import defaultdict

from config import load_config, DEFAULT_SETTING, get_channel_prompt, set_channel_prompt, delete_channel_prompt
from ai_client import create_ai_client, AIClient
from conversation_manager import ConversationManager
from utils import setup_logging, format_response_text, safe_send_message, validate_channel_access, extract_command_content, chunk_message

# 環境変数を読み込み
load_dotenv()

# ログ設定
logger = setup_logging(os.getenv("LOG_LEVEL", "INFO"))

class ChatBot:
    """メインのボットクラス"""
    
    def __init__(self):
        # 設定読み込み
        self.ai_config, self.discord_config, self.prompt_config = load_config()
        
        # コンポーネント初期化（プロバイダー別の引数を調整）
        provider_lower = self.ai_config.provider.lower()
        common_kwargs = dict(temperature=self.ai_config.temperature, max_tokens=self.ai_config.max_tokens)
        if provider_lower == "openai":
            self.ai_client = create_ai_client(
                provider_lower,
                api_key=self.ai_config.openai_api_key,
                model=self.ai_config.openai_model,
                **common_kwargs,
            )
        elif provider_lower == "ollama":
            self.ai_client = create_ai_client(
                provider_lower,
                base_url=self.ai_config.ollama_base_url,
                model=self.ai_config.ollama_model,
                **common_kwargs,
            )
        elif provider_lower == "gemini":
            self.ai_client = create_ai_client(
                provider_lower,
                api_key=self.ai_config.gemini_api_key,
                model=self.ai_config.gemini_model,
                **common_kwargs,
            )
        else:
            raise ValueError(f"Unsupported AI provider: {self.ai_config.provider}")

        # 表示用モデル名
        if provider_lower == "openai":
            self._display_model = self.ai_config.openai_model
        elif provider_lower == "ollama":
            self._display_model = self.ai_config.ollama_model
        elif provider_lower == "gemini":
            self._display_model = self.ai_config.gemini_model
        else:
            self._display_model = "unknown"
        
        self.conversation_manager = ConversationManager(max_history=self.ai_config.max_history)
        # スラッシュコマンド同期は一度だけ行う
        self._synced = False
        # チャンネル単位の同時実行ロック
        self._channel_locks = defaultdict(asyncio.Lock)
        
        # Discord Bot設定
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True  # ギルド情報の取得に必要
        
        # Bot初期化時にコマンドの自動同期を有効化
        # BOT_APPLICATION_ID が未設定/不正な場合は application_id を渡さない
        bot_kwargs = dict(
            command_prefix='/',
            intents=intents,
            sync_commands=True,  # コマンドの自動同期
            sync_commands_debug=True,  # デバッグ情報の出力
        )
        _app_id = os.getenv("BOT_APPLICATION_ID")
        if _app_id and _app_id.isdigit():
            bot_kwargs["application_id"] = int(_app_id)
        self.bot = commands.Bot(**bot_kwargs)
        
        # イベントハンドラー登録
        self._setup_events()
        
        # スラッシュコマンド登録
        self._setup_slash_commands()
        logger.info("スラッシュコマンドを設定しました")
        logger.info(f"登録されたコマンド数: {len(self.bot.tree.get_commands())}")
        for cmd in self.bot.tree.get_commands():
            logger.info(f"  - /{cmd.name}: {cmd.description}")
        
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

            # スラッシュコマンドを同期（一度だけ）
            try:
                if not self._synced:
                    logger.info("スラッシュコマンドの同期を開始...")
                    synced = await self.bot.tree.sync()
                    logger.info(f"グローバルスラッシュコマンドを同期しました: {len(synced)}個のコマンド")
                    for command in synced:
                        logger.info(f"  - /{command.name}: {command.description}")
                    if os.getenv("DEV_GUILD_ID"):
                        dev_guild_id = int(os.getenv("DEV_GUILD_ID"))
                        guild = discord.Object(id=dev_guild_id)
                        try:
                            dev_synced = await self.bot.tree.sync(guild=guild)
                            logger.info(f"開発ギルドでスラッシュコマンドを同期: {len(dev_synced)}個")
                        except Exception as dev_e:
                            logger.warning(f"開発ギルド同期に失敗: {dev_e}")
                    self._synced = True
            except Exception as e:
                logger.error(f"スラッシュコマンド同期中にエラー: {e}")

            # 登録チャンネルにログインメッセージを送信
            await self._send_login_message()

        @self.bot.event
        async def on_message(message):
            # 📝 すべてのメッセージをログに記録
            logger.info(
                f"[MESSAGE] Server: {message.guild.name if message.guild else 'DM'} | "
                f"Channel: #{message.channel.name if hasattr(message.channel, 'name') else 'DM'} ({message.channel.id}) | "
                f"Author: {message.author} ({message.author.id}) | "
                f"Bot: {message.author.bot} | "
                f"Content: {message.content}"
            )

            if message.author.bot:
                return

            # チャンネル権限確認
            if not validate_channel_access(message.channel.id, self.discord_config.channel_ids):
                return

            # コマンド処理を行う
            await self.bot.process_commands(message)
    
    def _setup_slash_commands(self):
        """スラッシュコマンドを設定"""
        
        @self.bot.tree.command(name="gpt", description="AIと対話します")
        async def gpt_command(interaction: discord.Interaction, prompt: str):
            """AIと対話するスラッシュコマンド"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
                await interaction.response.send_message("このチャンネルでは使用できません。", ephemeral=True)
                return
            
            await self._handle_ai_slash_command(interaction, prompt)
        
        @self.bot.tree.command(name="ai", description="AIと対話します（gptコマンドと同じ）")
        async def ai_command(interaction: discord.Interaction, prompt: str):
            """AIと対話するスラッシュコマンド（エイリアス）"""
            # チャンネル権限確認
            if not validate_channel_access(interaction.channel_id, self.discord_config.channel_ids):
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
    
    async def _handle_ai_slash_command(self, interaction: discord.Interaction, prompt: str):
        """AI対話スラッシュコマンドの処理"""
        channel_id = interaction.channel_id
        
        # ログ出力（ユーザー入力はマスク/短縮）
        safe_prompt = (prompt[:100] + "...") if len(prompt) > 100 else prompt
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"User: {interaction.user} ({interaction.user.id}) | Content: {prompt}")
        else:
            logger.info(f"User: {interaction.user} ({interaction.user.id}) | Content: {safe_prompt}")
        
        # 初回の場合はシステム設定を追加
        if not self.conversation_manager.get_messages(channel_id):
            current_setting = self.conversation_manager.get_system_setting(channel_id)
            if not current_setting:
                # チャンネル固有の設定があればそれを使用、なければデフォルト設定
                channel_prompt = get_channel_prompt(channel_id, self.prompt_config)
                self.conversation_manager.set_system_setting(channel_id, channel_prompt)
        
        try:
            # 1チャンネル1会話の直列化
            async with self._channel_locks[channel_id]:
                # ユーザーメッセージを履歴に追加
                self.conversation_manager.add_message(channel_id, "user", prompt)
                # 応答を遅延させる（処理時間が長い場合）
                await interaction.response.defer()

                # AI応答生成
                messages = self.conversation_manager.get_messages(channel_id)
                ai_response = await self.ai_client.generate_response(messages)

                # 応答を履歴に追加
                self.conversation_manager.add_message(channel_id, "assistant", ai_response)

                # 応答を整形して送信（長文は分割）
                formatted_response = format_response_text(ai_response)
                for part in chunk_message(formatted_response):
                    await interaction.followup.send(part)
            
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

        # 表示用のプロバイダー名を整形
        provider_name = {
            "openai": "OpenAI",
            "ollama": "Ollama",
            "gemini": "Gemini",
        }.get(self.ai_config.provider.lower(), self.ai_config.provider)

        show_text = f"""⚙️ **現在の設定 - <#{channel_id}>**

**AI設定:**
🔹 プロバイダー: `{provider_name}`
🔹 モデル: `{self._display_model}`
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

        # 表示用のプロバイダー名を整形
        provider_name = {
            "openai": "OpenAI",
            "ollama": "Ollama",
            "gemini": "Gemini",
        }.get(self.ai_config.provider.lower(), self.ai_config.provider)

        stats_text = f"""📊 **会話統計 - <#{channel_id}>**

💬 総メッセージ数: `{stats['total_messages']}件`
👤 ユーザーメッセージ: `{stats['user_messages']}件`
🤖 AIメッセージ: `{stats['assistant_messages']}件`
⚙️ システムメッセージ: `{stats['system_messages']}件`

**設定情報:**
🔹 AI プロバイダー: `{provider_name}`
🔹 モデル: `{self._display_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`"""

        await interaction.response.send_message(stats_text)
    
    async def _handle_help_slash_command(self, interaction: discord.Interaction):
        """ヘルプスラッシュコマンドの処理"""
        provider_name = {
            "openai": "OpenAI",
            "ollama": "Ollama",
            "gemini": "Gemini",
        }.get(self.ai_config.provider.lower(), self.ai_config.provider)

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

**現在の設定:**
🔹 AI プロバイダー: `{provider_name}`
🔹 モデル: `{self._display_model}`
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
    
    async def _send_login_message(self):
        """登録チャンネルにログインメッセージを送信"""
        if not self.discord_config.channel_ids:
            logger.info("チャンネル制限なし - ログインメッセージは送信しません")
            return
        
        # 表示用のプロバイダー名を整形
        provider_name = {
            "openai": "OpenAI",
            "ollama": "Ollama",
            "gemini": "Gemini",
        }.get(self.ai_config.provider.lower(), self.ai_config.provider)

        login_message = f"""🤖 **{self.bot.user.name} がログインしました！**

**AI設定情報:**
🔹 プロバイダー: `{provider_name}`
🔹 モデル: `{self._display_model}`
🔹 最大履歴: `{self.ai_config.max_history}件`
🔹 温度設定: `{self.ai_config.temperature}`

**利用可能なスラッシュコマンド:**
📝 `/gpt [prompt]` または `/ai [prompt]` - AIと対話
🔄 `/reset` - 会話履歴をリセット
⚙️ `/setting` グループ - プロンプト設定を管理
📊 `/stats` - 会話統計を表示
👁️ `/show` - 現在の設定を表示
❓ `/help` - ヘルプを表示

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