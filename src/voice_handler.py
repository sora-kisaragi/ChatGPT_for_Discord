"""
Voice Handler Module
ボイスチャンネルとの連携を行うモジュール
"""
import os
import json
import logging
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional

import discord
from discord import FFmpegPCMAudio

# ロガー設定
logger = logging.getLogger(__name__)

class VoiceSettings:
    """ユーザーとチャンネルの音声設定を管理するクラス"""
    
    def __init__(self, settings_file: str = None):
        """
        初期化
        
        Args:
            settings_file (str, optional): 設定ファイルのパス
        """
        self.settings_file = settings_file or os.path.join(tempfile.gettempdir(), "discord_bot_voice_settings.json")
        # 音声プリセット設定
        self.voice_presets = {
            "ultraman_x": {
                "name": "ウルトラマンX",
                "ref_audio_path": 'audio/ウルトラマン_X/vocal_Clipchamp_21lfph0q9.mp3.reformatted.wav_10.wav_0000250880_0000393920.wav',
                "prompt_text": '上木隊長、今アメリカを襲ったのはグリーザです。'
            }
            # 他のプリセットを追加可能
        }
        
        # ユーザーID/チャンネルIDごとのデフォルト設定
        # {"user_123456": "ultraman_x", "channel_789012": "ultraman_x"}
        self.default_settings = {}
        
        # 設定ファイルを読み込む
        self._load_settings()
    
    def _load_settings(self):
        """設定ファイルから設定を読み込む"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'presets' in data:
                        self.voice_presets.update(data['presets'])
                    if 'defaults' in data:
                        self.default_settings.update(data['defaults'])
                logger.info(f"音声設定を読み込みました: {len(self.voice_presets)} プリセット, {len(self.default_settings)} デフォルト設定")
        except Exception as e:
            logger.error(f"音声設定の読み込みエラー: {e}", exc_info=True)
    
    def _save_settings(self):
        """設定をファイルに保存"""
        try:
            data = {
                'presets': self.voice_presets,
                'defaults': self.default_settings
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"音声設定を保存しました: {self.settings_file}")
        except Exception as e:
            logger.error(f"音声設定の保存エラー: {e}", exc_info=True)
    
    def get_preset(self, preset_id: str) -> Dict[str, Any]:
        """
        プリセット情報を取得
        
        Args:
            preset_id (str): プリセットID
        
        Returns:
            Dict: プリセット情報
        """
        return self.voice_presets.get(preset_id, self.voice_presets.get("ultraman_x"))
    
    def get_all_presets(self) -> Dict[str, Dict[str, Any]]:
        """すべてのプリセットを取得"""
        return self.voice_presets
    
    def get_user_default(self, user_id: int) -> str:
        """ユーザーのデフォルト音声タイプを取得"""
        return self.default_settings.get(f"user_{user_id}", "ultraman_x")
    
    def get_channel_default(self, channel_id: int) -> str:
        """チャンネルのデフォルト音声タイプを取得"""
        return self.default_settings.get(f"channel_{channel_id}", "ultraman_x")
    
    def set_user_default(self, user_id: int, preset_id: str) -> bool:
        """
        ユーザーのデフォルト音声タイプを設定
        
        Args:
            user_id (int): ユーザーID
            preset_id (str): プリセットID
        
        Returns:
            bool: 成功したかどうか
        """
        if preset_id in self.voice_presets:
            self.default_settings[f"user_{user_id}"] = preset_id
            self._save_settings()
            return True
        return False
    
    def set_channel_default(self, channel_id: int, preset_id: str) -> bool:
        """
        チャンネルのデフォルト音声タイプを設定
        
        Args:
            channel_id (int): チャンネルID
            preset_id (str): プリセットID
        
        Returns:
            bool: 成功したかどうか
        """
        if preset_id in self.voice_presets:
            self.default_settings[f"channel_{channel_id}"] = preset_id
            self._save_settings()
            return True
        return False


class VoiceHandler:
    """音声処理ハンドラークラス"""
    
    def __init__(self, settings_file: str = None):
        """初期化"""
        self.voice_clients = {}  # サーバーIDをキーにしたボイスクライアント管理
        self.temp_dir = Path(tempfile.gettempdir()) / "discord_bot_voice"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 音声設定管理
        self.settings = VoiceSettings(settings_file)
    
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
    
    async def record_audio(self, guild_id, duration=5.0, user_id=None, silence_timeout=2.0, min_bytes=1000):
        """
        ボイスチャンネルの音声を録音し、一時ファイルに保存してパスを返す（RawDataSink使用）
        - duration: 最大録音秒数
        - silence_timeout: 無音とみなす秒数
        - min_bytes: 無音判定の最小バイト数
        """
        if guild_id not in self.voice_clients:
            logger.error(f"ボイスクライアントが見つかりません: Guild ID {guild_id}")
            return None
        voice_client = self.voice_clients[guild_id]
        try:
            import discord.sinks
        except ImportError:
            logger.error("discord.sinksが見つかりません。discord.py[voice]>=2.5.0が必要です。")
            return None

        sink = discord.sinks.RawDataSink()
        audio_file_path = self.temp_dir / f"recorded_{guild_id}.pcm"
        audio_data = bytearray()
        last_data_time = asyncio.get_event_loop().time()

        def on_data(sink, user, data):
            nonlocal last_data_time
            # user_id指定時はそのユーザーのみ録音
            if user_id is not None and user.id != user_id:
                return
            if len(data) >= min_bytes:
                last_data_time = asyncio.get_event_loop().time()
            audio_data.extend(data)

        sink.on('data', on_data)

        voice_client.start_recording(sink, finished_callback=None)
        logger.info(f"録音開始: Guild ID {guild_id}, 最大{duration}s, 無音{silence_timeout}sで終了")

        start_time = asyncio.get_event_loop().time()
        while True:
            await asyncio.sleep(0.1)
            now = asyncio.get_event_loop().time()
            if now - start_time > duration:
                logger.info("最大録音時間に到達したため録音終了")
                break
            if now - last_data_time > silence_timeout and len(audio_data) > 0:
                logger.info(f"無音({silence_timeout}s)検出で録音終了")
                break

        await voice_client.stop_recording()
        logger.info(f"録音終了: Guild ID {guild_id}")

        with open(audio_file_path, 'wb') as f:
            f.write(audio_data)
        logger.info(f"録音データを保存: {audio_file_path}")
        return str(audio_file_path)
    
    async def transcribe_audio(self, audio_file):
        """Whisperを使って音声をテキストに変換（将来実装）"""
        # TODO: Whisper APIで音声認識を実装
        logger.warning("音声認識機能は現在実装されていません")
        return "これはテスト用のテキストです。実際の音声認識は未実装です。"
    
    async def synthesize_speech(self, text, output_file=None, voice_preset=None, 
                          media_type='wav', user_id=None, channel_id=None):
        """
        テキストを音声に変換
        
        Args:
            text (str): 変換するテキスト
            output_file (str, optional): 出力ファイルパス
            voice_preset (str, optional): 音声プリセット名
            media_type (str, optional): 出力音声フォーマット ('wav' or 'mp3')
            user_id (int, optional): ユーザーID（プリセット未指定時に使用）
            channel_id (int, optional): チャンネルID（プリセット未指定時に使用）
            
        Returns:
            str or None: 生成された音声ファイルのパス、失敗時はNone
        """
        try:
            import requests
            
            if output_file is None:
                output_file = self.temp_dir / f"synth_{hash(text)}_{int(asyncio.get_event_loop().time())}.{media_type}"
            
            # 音声プリセットの決定
            # 1. 指定されたプリセット
            # 2. ユーザーのデフォルト設定
            # 3. チャンネルのデフォルト設定
            # 4. システムデフォルト (ultraman_x)
            if not voice_preset and user_id:
                voice_preset = self.settings.get_user_default(user_id)
            if not voice_preset and channel_id:
                voice_preset = self.settings.get_channel_default(channel_id)
            if not voice_preset:
                voice_preset = "ultraman_x"
            
            # プリセットデータを取得
            preset_data = self.settings.get_preset(voice_preset)
            
            # TTSのパラメータを設定
            params = {
                'text': text,
                'text_lang': 'ja',
                'ref_audio_path': preset_data["ref_audio_path"],
                'aux_ref_audio_paths': [],
                'prompt_text': preset_data["prompt_text"],
                'prompt_lang': 'ja',
                'top_k': 5,
                'top_p': 0.8,
                'temperature': 0.8,
                'text_split_method': 'cut3',
                'batch_size': 1,
                'batch_threshold': 0.75,
                'split_bucket': True,
                'speed_factor': 1.2,
                'fragment_interval': 0.3,
                'seed': -1,
                'media_type': media_type,
                'streaming_mode': 'false',
                'parallel_infer': True,
                'repetition_penalty': 2
            }
            
            logger.info(f"TTSリクエスト開始: テキスト '{text[:30]}...'")
            
            # TTSエンドポイントにGETリクエストを送信
            response = requests.get('http://127.0.0.1:9880/tts', params=params)
            
            # レスポンスの処理
            if response.status_code == 200:
                # 音声データをファイルに保存
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"TTSリクエスト成功: 音声ファイルを保存: {output_file}")
                return str(output_file)
            else:
                logger.error(f"TTSリクエストエラー: ステータス {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"音声合成エラー: {e}", exc_info=True)
            return None
