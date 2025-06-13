from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json
import openai
import anthropic
from src.core.config import settings


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key
        if self.api_key:
            openai.api_key = self.api_key
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        if not self.is_available():
            raise ValueError("OpenAI API key not configured")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await openai.ChatCompletion.acreate(
            model="gpt-4-turbo-preview",  # or gpt-3.5-turbo
            messages=messages,
            temperature=0.7,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content


class AnthropicProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.anthropic_api_key
        if self.api_key:
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
    
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 2000) -> str:
        if not self.is_available():
            raise ValueError("Anthropic API key not configured")
        
        # Claude uses a different message format
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        message = await self.client.messages.create(
            model="claude-3-opus-20240229",  # or claude-3-sonnet-20240229 for faster/cheaper
            max_tokens=max_tokens,
            temperature=0.7,
            messages=[
                {"role": "user", "content": full_prompt}
            ]
        )
        return message.content[0].text


class LLMService:
    """Service that manages multiple LLM providers"""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider()
        }
        self.default_provider = settings.default_llm_provider or "openai"
    
    def get_available_providers(self) -> List[str]:
        """Get list of configured providers"""
        return [name for name, provider in self.providers.items() if provider.is_available()]
    
    async def generate(
        self, 
        prompt: str, 
        system_prompt: str = None,
        provider: str = None,
        max_tokens: int = 2000
    ) -> str:
        """Generate text using specified or default provider"""
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        provider_instance = self.providers[provider_name]
        if not provider_instance.is_available():
            # Fallback to any available provider
            available = self.get_available_providers()
            if not available:
                raise ValueError("No LLM providers configured")
            provider_instance = self.providers[available[0]]
        
        return await provider_instance.generate(prompt, system_prompt, max_tokens)
