"""
ユーティリティ関数
"""
import logging
import asyncio
from typing import Optional, List
from pathlib import Path

def setup_logging(level: str = "INFO") -> logging.Logger:
    """ログ設定を初期化"""
    # ログディレクトリを作成
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / 'discord_bot.log', encoding='utf-8')
        ]
    )
    return logging.getLogger(__name__)

def format_response_text(text: str) -> str:
    """レスポンステキストを整形"""
    # 句点で改行を追加（分割は chunk_message に委譲）
    return text.replace('。', '。\n')

def chunk_message(text: str, limit: int = 2000) -> List[str]:
    """
    Discordのメッセージ上限に合わせて文字列をチャンクに分割
    """
    if text is None:
        return [""]
    if not text:
        return [""]
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        chunks.append(text[start:end])
        start = end
    return chunks

async def safe_send_message(channel, content: str, delay: float = 0.0):
    """安全にメッセージを送信（レート制限対応）"""
    if delay > 0:
        await asyncio.sleep(delay)
    
    try:
        await channel.send(content)
    except Exception as e:
        # discord.py の HTTPException(429) に簡易対応
        try:
            from discord.errors import HTTPException  # 遅延インポート
        except Exception:
            HTTPException = Exception  # フォールバック

        if isinstance(e, HTTPException) and getattr(e, "status", None) == 429:
            retry_after = float(getattr(e, "retry_after", 1.5) or 1.5)
            logging.warning(f"Rate limited (429). Retrying after {retry_after}s")
            await asyncio.sleep(retry_after)
            await channel.send(content)
        else:
            logging.error(f"Failed to send message: {e}")
            raise

def validate_channel_access(channel_id: int, allowed_channels: list) -> bool:
    """チャンネルアクセス権限を確認"""
    if not allowed_channels:  # 空の場合は全チャンネル許可
        return True
    return channel_id in allowed_channels

def extract_command_content(message_content: str, command: str) -> str:
    """コマンド部分を除去してコンテンツを抽出"""
    if message_content.startswith(command):
        content = message_content[len(command):].strip()
        return content
    return message_content
