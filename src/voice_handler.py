"""
Voice Handler Module
ボイスチャンネルとの連携を行うモジュール
"""
import os
import logging
import asyncio
import tempfile
from pathlib import Path

import discord
from discord import FFmpegPCMAudio

# ロガー設定
logger = logging.getLogger(__name__)

class VoiceHandler:
    """音声処理ハンドラークラス"""
    
    def __init__(self):
        """初期化"""
        self.voice_clients = {}  # サーバーIDをキーにしたボイスクライアント管理
        self.temp_dir = Path(tempfile.gettempdir()) / "discord_bot_voice"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def join_voice_channel(self, voice_channel):
        """ボイスチャンネルに接続"""
        try:
            # 既に接続している場合は切断
            if voice_channel.guild.id in self.voice_clients:
                await self.voice_clients[voice_channel.guild.id].disconnect()
                del self.voice_clients[voice_channel.guild.id]
                logger.info(f"既存の接続を切断: {voice_channel.guild.name}")
            
            # 新しく接続
            voice_client = await voice_channel.connect()
            self.voice_clients[voice_channel.guild.id] = voice_client
            logger.info(f"ボイスチャンネル接続成功: {voice_channel.name} ({voice_channel.guild.name})")
            return True
        except Exception as e:
            logger.error(f"ボイスチャンネル接続エラー: {e}", exc_info=True)
            return False
    
    async def leave_voice_channel(self, guild_id):
        """ボイスチャンネルから切断"""
        if guild_id in self.voice_clients:
            await self.voice_clients[guild_id].disconnect()
            del self.voice_clients[guild_id]
            logger.info(f"ボイスチャンネルから切断: Guild ID {guild_id}")
            return True
        return False
    
    async def play_audio(self, guild_id, audio_file):
        """音声ファイルを再生"""
        if guild_id not in self.voice_clients:
            logger.error(f"ボイスクライアントが見つかりません: Guild ID {guild_id}")
            return False
        
        voice_client = self.voice_clients[guild_id]
        
        # 既に再生中なら待機
        while voice_client.is_playing():
            await asyncio.sleep(0.5)
        
        try:
            voice_client.play(FFmpegPCMAudio(audio_file))
            logger.info(f"音声再生開始: {audio_file}")
            return True
        except Exception as e:
            logger.error(f"音声再生エラー: {e}", exc_info=True)
            return False
    
    async def record_audio(self, guild_id, duration=5.0):
        """音声を録音（将来実装）"""
        # TODO: Discord音声の録音機能を実装
        # 現在のDiscord.pyでは直接的な録音APIが提供されていないため、
        # 別の方法で実装する必要があります
        logger.warning("音声録音機能は現在実装されていません")
        return None
    
    async def transcribe_audio(self, audio_file):
        """Whisperを使って音声をテキストに変換（将来実装）"""
        # TODO: Whisper APIで音声認識を実装
        logger.warning("音声認識機能は現在実装されていません")
        return "これはテスト用のテキストです。実際の音声認識は未実装です。"
    
    async def synthesize_speech(self, text, output_file=None):
        """テキストを音声に変換（将来実装）"""
        # TODO: GPT-SoVITSで音声合成を実装
        if output_file is None:
            output_file = self.temp_dir / f"synth_{hash(text)}.mp3"
        
        logger.warning(f"音声合成機能は現在実装されていません: {text}")
        return None  # 実装時には音声ファイルのパスを返す
