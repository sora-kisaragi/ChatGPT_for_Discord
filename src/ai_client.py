"""
AI API クライアントの抽象化
"""
import asyncio
import aiohttp
import openai
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

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

def create_ai_client(provider: str, **config) -> AIClient:
    """設定に基づいてAIクライアントを作成"""
    if provider.lower() == "openai":
        return OpenAIClient(**config)
    elif provider.lower() == "ollama":
        return OllamaClient(**config)
    else:
        raise ValueError(f"Unsupported AI provider: {provider}")
