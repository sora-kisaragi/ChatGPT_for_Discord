"""
設定ファイル
"""
import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class AIConfig:
    """AI設定クラス"""
    provider: str = "ollama"  # "openai" または "ollama"
    
    # OpenAI設定
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    
    # Ollama設定
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    
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

# 環境変数から設定を読み込み
def load_config() -> tuple[AIConfig, DiscordConfig]:
    """環境変数または設定ファイルから設定を読み込む"""
    
    # AI設定
    ai_config = AIConfig(
        provider=os.getenv("AI_PROVIDER", "ollama"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        max_history=int(os.getenv("MAX_HISTORY", "10")),
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("MAX_TOKENS", "0")) or None
    )
    
    # Discord設定
    discord_config = DiscordConfig(
        token=os.getenv("DISCORD_TOKEN", ""),
        channel_ids=[int(x) for x in os.getenv("DISCORD_CHANNEL_IDS", "").split(",") if x.strip()]
    )
    
    return ai_config, discord_config

# デフォルト設定プロンプト
DEFAULT_SETTING = """セバスという執事を相手にした対話のシミュレーションを行います。
この会話は私たち複数人と、あなたセバスで会話を行います。

セバスの性格を下記に列挙します。
人格者であり弱者救済を是とする。
彼の善良さは「優しさ」ではなく「甘さ」
『悪』と見做した相手には本当に情け容赦が無い
黒の燕尾服を纏った、白髪白髭の古典的老執事
顔立ちは彫が深く、一見して柔らかくありながらも厳粛なイメージを持ち、その双眸は猛禽の様に鋭い。
両手には白い手袋を着けている。
王都に常駐していた頃は、その整った容姿と洗練された立ち居振舞いから年齢を問わず女性達にモテまくっていた。

口調は執事そのもので、いつも丁寧な言葉遣い。

上記例を参考に、セバスの性格や口調、言葉の作り方を模倣し、回答を構築してください。
ではシミュレーションを開始します。"""
