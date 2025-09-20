"""
設定ファイル
"""
import os
import json
import logging
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class AIConfig:
    """AI設定クラス"""
    provider: str = "ollama"  # "openai" / "ollama" / "gemini"
    
    # OpenAI設定
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    
    # Ollama設定
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Gemini 設定
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-pro"
    
    # 共通設定
    max_history: int = 10
    temperature: float = 0.7
    max_tokens: Optional[int] = None

@dataclass
class DiscordConfig:
    """Discord設定クラス"""
    token: str = ""
    channel_ids: List[int] = None
    
    def __post_init__(self):
        if self.channel_ids is None:
            self.channel_ids = []

@dataclass
class PromptConfig:
    """プロンプト設定クラス"""
    settings: dict = None
    
    def __post_init__(self):
        if self.settings is None:
            self.settings = {}

# 設定プロンプトの管理
SETTINGS_FILE = "config/prompt_settings.json"

def load_config() -> tuple[AIConfig, DiscordConfig, PromptConfig]:
    """環境変数または設定ファイルから設定を読み込む"""
    
    def safe_int(value: str, default: int) -> int:
        """安全に整数に変換"""
        try:
            return int(value) if value.strip() else default
        except (ValueError, AttributeError):
            return default
    
    def safe_float(value: str, default: float) -> float:
        """安全に浮動小数点に変換"""
        try:
            return float(value) if value.strip() else default
        except (ValueError, AttributeError):
            return default
    
    # AI設定
    ai_config = AIConfig(
        provider=os.getenv("AI_PROVIDER", "ollama"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        max_history=safe_int(os.getenv("MAX_HISTORY", "10"), 10),
        temperature=safe_float(os.getenv("TEMPERATURE", "0.7"), 0.7),
        max_tokens=safe_int(os.getenv("MAX_TOKENS", "0"), 0) or None
    )
    
    # Discord設定
    channel_ids_str = os.getenv("DISCORD_CHANNEL_IDS", "")
    channel_ids = []
    if channel_ids_str:
        try:
            channel_ids = [int(x.strip()) for x in channel_ids_str.split(",") if x.strip()]
        except ValueError:
            logger.warning(f"Invalid channel IDs format: {channel_ids_str}")
    
    discord_config = DiscordConfig(
        token=os.getenv("DISCORD_TOKEN", ""),
        channel_ids=channel_ids
    )
    
    # プロンプト設定読み込み
    prompt_config = load_prompt_settings()
    
    return ai_config, discord_config, prompt_config

def load_prompt_settings() -> PromptConfig:
    """プロンプト設定を読み込む"""
    settings_file = Path(SETTINGS_FILE)
    
    if settings_file.exists():
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return PromptConfig(settings=data)
        except Exception as e:
            logger.error(f"プロンプト設定の読み込みに失敗しました: {e}")
    
    return PromptConfig()

def save_prompt_settings(prompt_config: PromptConfig):
    """プロンプト設定を保存"""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(prompt_config.settings, f, ensure_ascii=False, indent=2)
        logger.info("プロンプト設定を保存しました")
    except Exception as e:
        logger.error(f"プロンプト設定の保存に失敗しました: {e}")

def get_channel_prompt(channel_id: int, prompt_config: PromptConfig) -> str:
    """チャンネル固有のプロンプトを取得"""
    return prompt_config.settings.get(str(channel_id), DEFAULT_SETTING)

def set_channel_prompt(channel_id: int, prompt: str, prompt_config: PromptConfig):
    """チャンネル固有のプロンプトを設定"""
    prompt_config.settings[str(channel_id)] = prompt
    save_prompt_settings(prompt_config)

def delete_channel_prompt(channel_id: int, prompt_config: PromptConfig):
    """チャンネル固有のプロンプトを削除（デフォルトに戻る）"""
    if str(channel_id) in prompt_config.settings:
        del prompt_config.settings[str(channel_id)]
        save_prompt_settings(prompt_config)

# デフォルト設定プロンプト
DEFAULT_SETTING = """あなたは有能なアシスタントです。ユーザーの質問に対して、丁寧かつ正確に答えてください。必要に応じて、具体例や詳細な説明を提供してください。
以下のルールに従ってください：
1. 常に礼儀正しく、親切に対応すること。
2. ユーザーの意図を正確に理解し、適切な回答を提供すること。
3. 不明な点がある場合は、確認の質問をすること。
4. 回答が不明確な場合は、正直に「わかりません」と答えること。
5. 可能な限り、最新の情報を提供すること。
6. ユーザーのプライバシーを尊重し、個人情報を求めないこと。
7. 不適切な内容や違法な要求には応じないこと。
8. 回答は簡潔かつ明確にすること。
9. 必要に応じて、参考資料やリンクを提供すること。
10. ユーザーが満足するまで、丁寧に対応し続けること。
これらのルールを守り、最高のサービスを提供してください。"""
