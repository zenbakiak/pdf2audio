#!/usr/bin/env python3

"""
PDF to Audio Converter

A modular Python package for converting PDF documents to audio using various
text-to-speech providers and LLM-powered text cleaning.
"""

from .config import Config
from .processors import PDFProcessor, ContentCleaner, TextToSpeechProcessor
from .llm_providers import LLMFactory, OpenAILLM, GeminiLLM
from .tts_providers import TTSFactory, GoogleTTS, OpenAITTS, AWSTTS

__version__ = "2.0.0"
__author__ = "zenbakiak"

# Public API
__all__ = [
    # Main classes
    'Config',
    'PDFProcessor', 
    'ContentCleaner',
    'TextToSpeechProcessor',
    
    # Factories
    'LLMFactory',
    'TTSFactory',
    
    # LLM Providers
    'OpenAILLM',
    'GeminiLLM',
    
    # TTS Providers
    'GoogleTTS',
    'OpenAITTS', 
    'AWSTTS',
]