"""
会話履歴管理クラス
"""
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ConversationManager:
    """会話履歴を管理するクラス"""
    
    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.conversations: Dict[int, List[Dict[str, str]]] = {}  # チャンネルIDごとの履歴
        self.system_settings: Dict[int, str] = {}  # チャンネルIDごとのシステム設定
    
    def get_messages(self, channel_id: int) -> List[Dict[str, str]]:
        """指定チャンネルの会話履歴を取得"""
        return self.conversations.get(channel_id, [])
    
    def add_message(self, channel_id: int, role: str, content: str):
        """メッセージを追加"""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        message = {"role": role, "content": content}
        self.conversations[channel_id].append(message)
        
        # 履歴制限を適用
        self._trim_history(channel_id)
    
    def set_system_setting(self, channel_id: int, setting: str):
        """システム設定を更新"""
        self.system_settings[channel_id] = setting
        
        # 既存の会話履歴をクリアして新しいシステムメッセージを設定
        self.conversations[channel_id] = []
        if setting:
            self.conversations[channel_id].append({"role": "system", "content": setting})
    
    def get_system_setting(self, channel_id: int) -> Optional[str]:
        """システム設定を取得"""
        return self.system_settings.get(channel_id)
    
    def reset_conversation(self, channel_id: int, new_setting: Optional[str] = None):
        """会話履歴をリセット"""
        self.conversations[channel_id] = []
        
        if new_setting is not None:
            self.system_settings[channel_id] = new_setting
        
        # システムメッセージを追加
        current_setting = self.system_settings.get(channel_id)
        if current_setting:
            self.conversations[channel_id].append({"role": "system", "content": current_setting})
    
    def _trim_history(self, channel_id: int):
        """履歴を制限内に収める"""
        messages = self.conversations[channel_id]
        
        if len(messages) <= self.max_history:
            return
        
        # システムメッセージを保持しながら古いメッセージを削除
        system_messages = [msg for msg in messages if msg["role"] == "system"]
        non_system_messages = [msg for msg in messages if msg["role"] != "system"]
        
        # 最新のメッセージを保持（システムメッセージ分を除く）
        keep_count = self.max_history - len(system_messages)
        if keep_count > 0:
            non_system_messages = non_system_messages[-keep_count:]
        else:
            non_system_messages = []
        
        # システムメッセージを先頭に配置
        self.conversations[channel_id] = system_messages + non_system_messages
        
        logger.info(f"Channel {channel_id}: Trimmed history to {len(self.conversations[channel_id])} messages")
    
    def get_conversation_stats(self, channel_id: int) -> Dict[str, int]:
        """会話統計を取得"""
        messages = self.conversations.get(channel_id, [])
        return {
            "total_messages": len(messages),
            "user_messages": len([m for m in messages if m["role"] == "user"]),
            "assistant_messages": len([m for m in messages if m["role"] == "assistant"]),
            "system_messages": len([m for m in messages if m["role"] == "system"])
        }
