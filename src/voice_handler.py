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
            },
            "floyd_leech": {
                "name": "フロイド・リーチ",
                "ref_audio_path": 'audio/フロイド/vocal_ツイステ小エビが大好きなフロイドボイス集フロイド - from YouTubet2k2elij.mp3_10.flac_0002547520_0002771520.wav',
                "prompt_text": 'オンボロ寮のゴーストってクラゲみたい話してみたいから今度小指ちゃんのとこに泊めてよぉ。'
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
                        # フロイド設定の詳細をログ出力
                        if 'floyd_leech' in data['presets']:
                            floyd_data = data['presets']['floyd_leech']
                            logger.info(f"設定ファイルからのフロイド設定: ref_audio_path={floyd_data.get('ref_audio_path')}, prompt_text={floyd_data.get('prompt_text')}")
                    if 'defaults' in data:
                        self.default_settings.update(data['defaults'])
                logger.info(f"音声設定を読み込みました: {len(self.voice_presets)} プリセット, {len(self.default_settings)} デフォルト設定")
                # フロイド設定の現在の状態をログ出力
                if 'floyd_leech' in self.voice_presets:
                    floyd_data = self.voice_presets['floyd_leech']
                    logger.info(f"読み込み後のフロイド設定: ref_audio_path={floyd_data.get('ref_audio_path')}, prompt_text={floyd_data.get('prompt_text')}")
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
    
    def __init__(self, settings_file: str = None, reset_settings: bool = False):
        """
        初期化
        
        Args:
            settings_file (str, optional): 設定ファイルのパス
            reset_settings (bool, optional): 起動時に設定ファイルをリセットするかどうか
        """
        self.voice_clients = {}  # サーバーIDをキーにしたボイスクライアント管理
        self.temp_dir = Path(tempfile.gettempdir()) / "discord_bot_voice"
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 設定ファイルのパス
        settings_path = settings_file or os.path.join(tempfile.gettempdir(), "discord_bot_voice_settings.json")
        
        # 設定ファイルをリセットする場合
        if reset_settings and os.path.exists(settings_path):
            try:
                os.remove(settings_path)
                logger.info(f"設定ファイルをリセットしました: {settings_path}")
            except Exception as e:
                logger.error(f"設定ファイルのリセットに失敗しました: {e}", exc_info=True)
        
        # 音声設定管理
        self.settings = VoiceSettings(settings_file)
        
    def reload_settings(self):
        """設定を再読み込みする"""
        return self.settings._load_settings()
    
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
    
    async def play_audio(self, guild_id, audio_file, delete_after_play=True):
        """
        音声ファイルを再生
        
        Args:
            guild_id: サーバーID
            audio_file: 再生する音声ファイルパス
            delete_after_play: 再生後にファイルを削除するかどうか
        """
        if guild_id not in self.voice_clients:
            logger.error(f"ボイスクライアントが見つかりません: Guild ID {guild_id}")
            return False
        
        voice_client = self.voice_clients[guild_id]
        
        # 既に再生中なら待機
        while voice_client.is_playing():
            await asyncio.sleep(0.5)
        
        try:
            # 再生
            voice_client.play(FFmpegPCMAudio(audio_file))
            logger.info(f"音声再生開始: {audio_file}")
            
            # 再生終了を待機するタスクを作成
            if delete_after_play:
                asyncio.create_task(self._wait_and_delete_audio(voice_client, audio_file))
                
            return True
        except Exception as e:
            logger.error(f"音声再生エラー: {e}", exc_info=True)
            return False
            
    async def _wait_and_delete_audio(self, voice_client, audio_file):
        """
        音声再生の終了を待って、ファイルを削除する
        
        Args:
            voice_client: ボイスクライアント
            audio_file: 削除する音声ファイルパス
        """
        # 再生が終わるまで待機
        while voice_client.is_playing():
            await asyncio.sleep(0.5)
            
        # さらに少し待機してから削除
        await asyncio.sleep(1.0)
        
        # ファイルを削除
        await self._delete_file_after_delay(audio_file, delay=0)
    
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
        
    async def _delete_file_after_delay(self, file_path, delay=5.0):
        """
        指定した遅延後にファイルを削除する
        
        Args:
            file_path (str): 削除するファイルのパス
            delay (float): 削除までの遅延時間（秒）
        """
        try:
            # 指定時間待機（この間にファイルが使用される）
            await asyncio.sleep(delay)
            
            # ファイルが存在するかチェック
            if os.path.exists(file_path):
                # ファイルを削除
                os.remove(file_path)
                logger.info(f"一時ファイルを削除しました: {file_path}")
            else:
                logger.warning(f"削除対象ファイルが見つかりません: {file_path}")
        except Exception as e:
            logger.error(f"ファイル削除エラー: {e}", exc_info=True)
    
    async def update_tts_weights(self, voice_preset):
        """
        TTSサーバーの重みファイルを更新する
        
        Args:
            voice_preset (str): 音声プリセット名
            
        Returns:
            bool: 更新に成功したかどうか
        """
        try:
            import requests
            
            # プリセットに対応する重みファイルのパス設定
            weights_settings = {
                "ultraman_x": {
                    "gpt_weights": "GPT_weights/ULTRAMAN_X-e15.ckpt",
                    "sovits_weights": "SoVITS_weights/ULTRAMAN_X_e8_s200.pth"
                },
                "floyd_leech": {
                    "gpt_weights": "GPT_weights/floyd-e15.ckpt",
                    "sovits_weights": "SoVITS_weights/floyd_e8_s64.pth"
                }
                # 他のプリセットを追加可能
            }
            
            # 指定されたプリセットの設定がない場合はデフォルト値を使用
            if voice_preset not in weights_settings:
                logger.warning(f"プリセット '{voice_preset}' の重み設定が見つかりません。デフォルト設定を使用します。")
                voice_preset = "ultraman_x"
                
            # GPT重みの設定更新
            gpt_weights_path = weights_settings[voice_preset]["gpt_weights"]
            gpt_response = requests.get(
                'http://127.0.0.1:9880/set_gpt_weights',
                params={'t2s_weights_path': gpt_weights_path}
            )
            
            # SoVITS重みの設定更新
            sovits_weights_path = weights_settings[voice_preset]["sovits_weights"]
            sovits_response = requests.get(
                'http://127.0.0.1:9880/set_sovits_weights',
                params={'vits_weights_path': sovits_weights_path}
            )
            
            # レスポンスの確認
            if gpt_response.status_code == 200 and sovits_response.status_code == 200:
                logger.info(f"TTSサーバーの重み設定を更新しました: プリセット '{voice_preset}'")
                logger.info(f"GPT重み: {gpt_weights_path}")
                logger.info(f"SoVITS重み: {sovits_weights_path}")
                return True
            else:
                logger.error(f"TTSサーバーの重み設定更新に失敗しました: GPT({gpt_response.status_code}), SoVITS({sovits_response.status_code})")
                return False
                
        except Exception as e:
            logger.error(f"TTSサーバーの重み設定更新エラー: {e}", exc_info=True)
            return False
    
    async def synthesize_speech(self, text, output_file=None, voice_preset=None, 
                          media_type='wav', user_id=None, channel_id=None, delete_after_use=True):
        """
        テキストを音声に変換
        
        Args:
            text (str): 変換するテキスト
            output_file (str, optional): 出力ファイルパス
            voice_preset (str, optional): 音声プリセット名
            media_type (str, optional): 出力音声フォーマット ('wav' or 'mp3')
            user_id (int, optional): ユーザーID（プリセット未指定時に使用）
            channel_id (int, optional): チャンネルID（プリセット未指定時に使用）
            delete_after_use (bool, optional): 生成後に音声ファイルを削除するかどうか
            
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
            
            # フロイドの場合は最新の設定を強制的に使用
            if voice_preset == "floyd_leech":
                preset_data = {
                    "name": "フロイド・リーチ",
                    "ref_audio_path": 'audio/フロイド/vocal_ツイステ小エビが大好きなフロイドボイス集フロイド - from YouTubet2k2elij.mp3_10.flac_0002547520_0002771520.wav',
                    "prompt_text": 'オンボロ寮のゴーストってクラゲみたい話してみたいから今度小指ちゃんのとこに泊めてよぉ。'
                }
                logger.info("フロイド設定を強制的に上書きしました")
            
            # TTSサーバーの重み設定を更新
            await self.update_tts_weights(voice_preset)
            
            # TTSのパラメータを設定
            params = {
                'text': text,
                'text_lang': 'ja',
                'ref_audio_path': preset_data["ref_audio_path"],
                'aux_ref_audio_paths': [],
                'prompt_text': preset_data["prompt_text"],
                'prompt_lang': 'ja',
                'top_k': 5,
                'top_p': 0.9,
                'temperature': 1,
                'text_split_method': 'cut5',
                'batch_size': 4,
                'batch_threshold': 0.75,
                'split_bucket': True,
                'speed_factor': 1.0,
                'fragment_interval': 0.3,
                'seed': -1,
                'media_type': media_type,
                'streaming_mode': 'false',
                'parallel_infer': True,
                'repetition_penalty': 2
            }
            
            logger.info(f"TTSリクエスト開始: テキスト '{text[:30]}...'")
            
            # デバッグ用にパラメータをログ出力
            logger.info(f"TTSリクエストパラメータ: voice_preset={voice_preset}, ref_audio_path={preset_data['ref_audio_path']}, prompt_text={preset_data['prompt_text']}")
            
            # TTSエンドポイントにGETリクエストを送信
            response = requests.get('http://127.0.0.1:9880/tts', params=params)
            
            # レスポンスの処理
            if response.status_code == 200:
                # 音声データをファイルに保存
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                logger.info(f"TTSリクエスト成功: 音声ファイルを保存: {output_file}")
                
                # ファイルパスを返す
                file_path = str(output_file)
                
                # 削除フラグが立っている場合は、返却後に削除するための関数を設定
                if delete_after_use:
                    # このファイルは使用後に削除対象とマーク
                    asyncio.create_task(self._delete_file_after_delay(file_path))
                    
                return file_path
            else:
                logger.error(f"TTSリクエストエラー: ステータス {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"音声合成エラー: {e}", exc_info=True)
            return None
