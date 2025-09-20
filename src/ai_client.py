"""
AI API クライアントの抽象化
"""
import asyncio
import aiohttp
import openai
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

# Gemini SDK (optional)
try:
    import google.generativeai as genai  # type: ignore
except Exception:
    genai = None  # type: ignore

logger = logging.getLogger(__name__)

class AIClient(ABC):
    """AI API クライアントの抽象基底クラス"""
    
    @abstractmethod
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """メッセージリストから応答を生成する"""
        pass

class OpenAIClient(AIClient):
    """OpenAI API クライアント"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo", **kwargs):
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", None)
        self.client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """OpenAI APIを使用して応答を生成"""
        try:
            # 新しいOpenAI APIクライアントを使用
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

class OllamaClient(AIClient):
    """Ollama API クライアント"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1", **kwargs):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", None)
    
    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Ollama APIを使用して応答を生成"""
        url = f"{self.base_url}/api/chat"
        
        # Ollamaの形式に変換
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.temperature,
            }
        }
        
        if self.max_tokens:
            payload["options"]["num_predict"] = self.max_tokens
        
        # 追加のオプションをマージ
        if "options" in kwargs:
            payload["options"].update(kwargs["options"])
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=60)) as session:
                async with session.post(url, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API error {response.status}: {error_text}")
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
                    data = await response.json()
                    
                    # レスポンス形式の検証
                    if "message" not in data or "content" not in data["message"]:
                        logger.error(f"Invalid Ollama response format: {data}")
                        raise Exception("Invalid response format from Ollama API")
                    
                    return data["message"]["content"]
        except aiohttp.ClientError as e:
            logger.error(f"Ollama API connection error: {e}")
            raise Exception(f"Ollama APIへの接続に失敗しました: {e}")
        except asyncio.TimeoutError:
            logger.error("Ollama API timeout")
            raise Exception("Ollama API request timed out")
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

class GeminiClient(AIClient):
    """Google Gemini API クライアント"""

    def __init__(self, api_key: str, model: str = "gemini-1.5-pro", **kwargs):
        if genai is None:
            raise ImportError(
                "google-generativeai がインストールされていません。requirements.txt をインストールしてください。"
            )
        self.api_key = api_key
        self.model = model
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", None)  # Gemini は max_output_tokens
        genai.configure(api_key=api_key)

    @staticmethod
    def _convert_history(messages: List[Dict[str, str]]):
        """OpenAI 形式の履歴を Gemini の history/system に変換"""
        system_instruction: Optional[str] = None
        history: List[Dict[str, Any]] = []
        current_input: str = ""

        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system" and system_instruction is None:
                system_instruction = content
            elif role in ("user", "assistant"):
                g_role = "user" if role == "user" else "model"
                history.append({"role": g_role, "parts": [content]})

        # 直近のユーザー入力を現在の入力として使用
        for m in reversed(messages):
            if m.get("role") == "user":
                current_input = m.get("content", "")
                break

        # 現在入力を history の最後に含めないようにする（Gemini の send_message に渡す）
        if history and current_input and history[-1]["role"] == "user" and history[-1]["parts"][0] == current_input:
            history = history[:-1]

        return system_instruction, history, current_input

    async def generate_response(self, messages: List[Dict[str, str]], **kwargs) -> str:
        system_instruction, history, current_input = self._convert_history(messages)

        if not current_input:
            current_input = "\n\n".join(m.get("content", "") for m in messages if m.get("role") == "user")

        generation_config = {"temperature": self.temperature}
        if self.max_tokens:
            generation_config["max_output_tokens"] = self.max_tokens

        def _run_blocking() -> str:
            model = genai.GenerativeModel(
                self.model,
                system_instruction=system_instruction if system_instruction else None,
            )
            chat = model.start_chat(history=history)
            resp = chat.send_message(current_input, generation_config=generation_config)
            return getattr(resp, "text", "") or ""

        try:
            text = await asyncio.to_thread(_run_blocking)
            if not text:
                raise Exception("Gemini から空の応答が返されました")
            return text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

def create_ai_client(provider: str, **config) -> AIClient:
    """設定に基づいてAIクライアントを作成"""
    if provider.lower() == "openai":
        return OpenAIClient(**config)
    elif provider.lower() == "ollama":
        return OllamaClient(**config)
    elif provider.lower() == "gemini":
        return GeminiClient(**config)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
