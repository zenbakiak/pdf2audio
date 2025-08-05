#!/usr/bin/env python3

from abc import ABC, abstractmethod
import os
from typing import Optional
from openai import OpenAI
import google.generativeai as genai
from .config import Config


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Config):
        self.config = config
    
    @abstractmethod
    def clean_text(self, text: str) -> str:
        """Clean text using the LLM provider."""
        pass

    @abstractmethod
    def apply_ssml(self, text: str) -> str:
        """Apply SSML tags to the text using the LLM provider."""
        pass


class OpenAILLM(LLMProvider):
    """OpenAI LLM provider for text cleaning."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """Create OpenAI client."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client. Please ensure your 'openai' library is up to date and OPENAI_API_KEY is set. Error: {e}")
    
    def clean_text(self, text: str) -> str:
        """Clean text using OpenAI."""
        if not text:
            return text
        
        llm_config = self.config.get_llm_config('openai')
        prompt = self.config.cleaning_prompt
        
        try:
            response = self.client.chat.completions.create(
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are a text cleaning assistant."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=llm_config.get('max_tokens', 4000),
                temperature=llm_config.get('temperature', 0.1)
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if self.config.verbose:
                print(f"Error cleaning text with OpenAI: {e}")
                print("Proceeding with original text...")
            return text

    def apply_ssml(self, text: str) -> str:
        """Apply SSML tags to the text using OpenAI."""
        if not text:
            return text
        
        llm_config = self.config.get_llm_config('openai')
        prompt = self.config.ssml_prompt
        
        try:
            response = self.client.chat.completions.create(
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You are an SSML tagging assistant."}, 
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=llm_config.get('max_tokens', 4000),
                temperature=llm_config.get('temperature', 0.1)
            )
            
            return response.choices[0].message.content
        except Exception as e:
            if self.config.verbose:
                print(f"Error applying SSML with OpenAI: {e}")
                print("Proceeding with original text...")
            return text


class GeminiLLM(LLMProvider):
    """Google Gemini LLM provider for text cleaning."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self._configure_gemini()
    
    def _configure_gemini(self) -> None:
        """Configure Gemini API."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
    
    def clean_text(self, text: str) -> str:
        """Clean text using Gemini."""
        if not text:
            return text
        
        llm_config = self.config.get_llm_config('gemini')
        prompt = self.config.cleaning_prompt
        
        try:
            model = genai.GenerativeModel(llm_config.get('model', 'gemini-pro'))
            response = model.generate_content(f"{prompt}\n\n{text}")
            return response.text
        except Exception as e:
            if self.config.verbose:
                print(f"Error cleaning text with Gemini: {e}")
                print("Proceeding with original text...")
            return text

    def apply_ssml(self, text: str) -> str:
        """Apply SSML tags to the text using Gemini."""
        if not text:
            return text
        
        llm_config = self.config.get_llm_config('gemini')
        prompt = self.config.ssml_prompt
        
        try:
            model = genai.GenerativeModel(llm_config.get('model', 'gemini-pro'))
            response = model.generate_content(f"{prompt}\n\n{text}")
            return response.text
        except Exception as e:
            if self.config.verbose:
                print(f"Error applying SSML with Gemini: {e}")
                print("Proceeding with original text...")
            return text


class LLMFactory:
    """Factory for creating LLM providers."""
    
    @staticmethod
    def create_provider(provider_name: str, config: Config) -> LLMProvider:
        """Create LLM provider based on name."""
        providers = {
            'openai': OpenAILLM,
            'gemini': GeminiLLM
        }
        
        provider_class = providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
        
        return provider_class(config)