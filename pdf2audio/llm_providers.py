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
        pass

    @abstractmethod
    def apply_ssml(self, text: str) -> str:
        pass

    @abstractmethod
    def summarize_text(self, text: str, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        pass

    @abstractmethod
    def merge_summaries(self, text: str, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        pass

    @abstractmethod
    def expand_summary(self, summary: str, source: Optional[str] = None, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        pass


class OpenAILLM(LLMProvider):
    def __init__(self, config: Config):
        super().__init__(config)
        self.client = self._create_client()

    def _create_client(self) -> OpenAI:
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client. Error: {e}")

    def clean_text(self, text: str) -> str:
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

    def summarize_text(self, text: str, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        if not text:
            return text
        llm_config = self.config.get_llm_config('openai')
        base = self.config.get('llm.summary_prompt', 'Summarize this text for an audiobook:')
        lang_note = f"\nWrite the summary in {language}." if language else ""
        length_note = f"\nTarget length: at least {target_words} words." if target_words else ""
        prompt = f"{base}{lang_note}{length_note}"
        try:
            response = self.client.chat.completions.create(
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You produce concise, coherent audiobook-style summaries."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=llm_config.get('max_tokens', 4000),
                temperature=llm_config.get('temperature', 0.3)
            )
            return response.choices[0].message.content
        except Exception as e:
            if self.config.verbose:
                print(f"Error summarizing with OpenAI: {e}")
                print("Proceeding with original text...")
            return text

    def merge_summaries(self, text: str, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        if not text:
            return text
        llm_config = self.config.get_llm_config('openai')
        base = self.config.get('llm.summary_merge_prompt', 'Merge the following chunk summaries into one cohesive audiobook-style summary without repetition:')
        lang_note = f"\nWrite the final summary in {language}." if language else ""
        length_note = f"\nDo not shorten; target overall length ≥ {target_words} words." if target_words else ""
        prompt = f"{base}{lang_note}{length_note}"
        try:
            response = self.client.chat.completions.create(
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You merge and compress summaries into a single coherent narrative without losing details."},
                    {"role": "user", "content": f"{prompt}\n\n{text}"}
                ],
                max_tokens=llm_config.get('max_tokens', 4000),
                temperature=llm_config.get('temperature', 0.2)
            )
            return response.choices[0].message.content
        except Exception as e:
            if self.config.verbose:
                print(f"Error merging summaries with OpenAI: {e}")
                print("Returning concatenated summaries...")
            return text

    def expand_summary(self, summary: str, source: Optional[str] = None, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        llm_config = self.config.get_llm_config('openai')
        target_note = f"Expand to at least {target_words} words while staying faithful to the source." if target_words else "Expand with more detail while staying faithful to the source."
        lang_note = f" Write in {language}." if language else ""
        src = f"\n\nSource points (for fidelity):\n{source}" if source else ""
        prompt = f"The following summary is too short. {target_note}{lang_note}\n\nSummary to expand:\n{summary}{src}"
        try:
            response = self.client.chat.completions.create(
                model=llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": "You expand summaries by adding missing but consistent detail; no hallucinations."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=llm_config.get('max_tokens', 4000),
                temperature=llm_config.get('temperature', 0.3)
            )
            return response.choices[0].message.content
        except Exception as e:
            if self.config.verbose:
                print(f"Error expanding summary with OpenAI: {e}")
            return summary


class GeminiLLM(LLMProvider):
    def __init__(self, config: Config):
        super().__init__(config)
        self._configure_gemini()

    def _configure_gemini(self) -> None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        genai.configure(api_key=api_key)

    def clean_text(self, text: str) -> str:
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

    def summarize_text(self, text: str, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        if not text:
            return text
        llm_config = self.config.get_llm_config('gemini')
        base = self.config.get('llm.summary_prompt', 'Summarize this text for an audiobook:')
        lang_note = f"\nWrite the summary in {language}." if language else ""
        length_note = f"\nTarget length: at least {target_words} words." if target_words else ""
        prompt = f"{base}{lang_note}{length_note}"
        try:
            model = genai.GenerativeModel(llm_config.get('model', 'gemini-pro'))
            response = model.generate_content(f"{prompt}\n\n{text}")
            return response.text
        except Exception as e:
            if self.config.verbose:
                print(f"Error summarizing with Gemini: {e}")
                print("Proceeding with original text...")
            return text

    def merge_summaries(self, text: str, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        if not text:
            return text
        llm_config = self.config.get_llm_config('gemini')
        base = self.config.get('llm.summary_merge_prompt', 'Merge the following chunk summaries into one cohesive audiobook-style summary without repetition:')
        lang_note = f"\nWrite the final summary in {language}." if language else ""
        length_note = f"\nDo not shorten; target overall length ≥ {target_words} words." if target_words else ""
        prompt = f"{base}{lang_note}{length_note}"
        try:
            model = genai.GenerativeModel(llm_config.get('model', 'gemini-pro'))
            response = model.generate_content(f"{prompt}\n\n{text}")
            return response.text
        except Exception as e:
            if self.config.verbose:
                print(f"Error merging summaries with Gemini: {e}")
                print("Returning concatenated summaries...")
            return text

    def expand_summary(self, summary: str, source: Optional[str] = None, language: Optional[str] = None, target_words: Optional[int] = None) -> str:
        llm_config = self.config.get_llm_config('gemini')
        target_note = f"Expand to at least {target_words} words while staying faithful to the source." if target_words else "Expand with more detail while staying faithful to the source."
        lang_note = f" Write in {language}." if language else ""
        src = f"\n\nSource points (for fidelity):\n{source}" if source else ""
        prompt = f"The following summary is too short. {target_note}{lang_note}\n\nSummary to expand:\n{summary}{src}"
        try:
            model = genai.GenerativeModel(llm_config.get('model', 'gemini-pro'))
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if self.config.verbose:
                print(f"Error expanding summary with Gemini: {e}")
            return summary


class LLMFactory:
    @staticmethod
    def create_provider(provider_name: str, config: Config) -> LLMProvider:
        providers = {
            'openai': OpenAILLM,
            'gemini': GeminiLLM
        }
        provider_class = providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
        return provider_class(config)

