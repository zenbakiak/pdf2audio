#!/usr/bin/env python3

from typing import Optional
import os
from .config import Config
from .llm_providers import LLMFactory
from .tts_providers import TTSFactory


class ContentCleaner:
    """High-level wrapper for text cleaning using various LLM providers."""
    
    def __init__(self, config: Config):
        self.config = config
        self._provider = None
    
    @property
    def provider(self):
        """Lazy load the LLM provider."""
        if self._provider is None:
            provider_name = self.config.llm_provider
            self._provider = LLMFactory.create_provider(provider_name, self.config)
        return self._provider
    
    def clean(self, text: str) -> str:
        """
        Clean text using the configured LLM provider.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text ready for TTS conversion
        """
        if not text:
            return text
        
        if self.config.verbose:
            print(f"Cleaning text with {self.config.llm_provider}...")
        
        return self.provider.clean_text(text)

    def apply_ssml(self, text: str) -> str:
        """
        Apply SSML tags to the text using the configured LLM provider.
        
        Args:
            text: Cleaned text to be enhanced with SSML
            
        Returns:
            Text with SSML tags
        """
        if not text:
            return text
        
        if self.config.verbose:
            print(f"Applying SSML with {self.config.llm_provider}...")
        
        return self.provider.apply_ssml(text)
    
    def set_provider(self, provider_name: str) -> None:
        """
        Switch to a different LLM provider.
        
        Args:
            provider_name: Name of the provider ('openai' or 'gemini')
        """
        self.config.set('llm.provider', provider_name)
        self._provider = None  # Force reload on next access


class TextToSpeechProcessor:
    """High-level wrapper for text-to-speech using various TTS providers."""
    
    def __init__(self, config: Config):
        self.config = config
        self._provider = None
    
    @property
    def provider(self):
        """Lazy load the TTS provider."""
        if self._provider is None:
            provider_name = self.config.tts_provider
            self._provider = TTSFactory.create_provider(provider_name, self.config)
        return self._provider
    
    def synthesize(self, text: str, output_path: str, language: Optional[str] = None) -> None:
        """
        Convert text to speech using the configured TTS provider.
        
        Args:
            text: Text to convert to speech
            output_path: Path where to save the audio file
            language: Language code (optional, uses config default)
        """
        if not text:
            raise ValueError("Text cannot be empty")
        
        # Use provided language or get from config
        lang_code = language or self.config.default_language
        
        # Apply language mappings
        lang_code = self.config.get_language_mapping(lang_code)
        
        if self.config.verbose:
            provider_name = self.config.tts_provider
            print(f"Using TTS provider: {provider_name}")
            
            # Show voice settings
            voice_config = self.config.get_tts_config(provider_name)
            if voice_config:
                print(f"Voice settings: {voice_config}")
        
        # Validate speaking rate if it's not 1.0
        speaking_rate = self.config.speaking_rate
        if speaking_rate != 1.0:
            from tts_providers import validate_speaking_rate
            validate_speaking_rate(speaking_rate)
        
        if self.config.verbose:
            print(f"Converting text to speech (language: {lang_code})")
        
        # Synthesize audio
        self.provider.synthesize(text, output_path, lang_code)
        
        if self.config.verbose:
            print(f"Audio saved to: {output_path}")
    
    def set_provider(self, provider_name: str) -> None:
        """
        Switch to a different TTS provider.
        
        Args:
            provider_name: Name of the provider ('gtts', 'openai', or 'aws')
        """
        self.config.set('tts.provider', provider_name)
        self._provider = None  # Force reload on next access


class PDFProcessor:
    """High-level processor that combines PDF extraction, cleaning, and TTS conversion."""
    
    def __init__(self, config: Config):
        self.config = config
        self.content_cleaner = ContentCleaner(config)
        self.tts_processor = TextToSpeechProcessor(config)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF file."""
        import pdfplumber
        
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            raise RuntimeError(f"Error extracting text from PDF: {e}")
        
        return text.strip()
    
    def save_text_file(self, text: str, base_path: str, suffix: str) -> None:
        """Save text to file with given suffix."""
        text_path = base_path.replace('.mp3', f'_{suffix}.txt')
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        if self.config.verbose:
            print(f"Text saved to: {text_path}")
    
    def validate_paths(self, pdf_path: str, output_path: str) -> None:
        """Validate input PDF exists and create output directory if needed."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
    
    def process(self, pdf_path: str, output_path: str, 
                language: Optional[str] = None, skip_cleaning: bool = False) -> None:
        """
        Complete PDF to audio processing pipeline.
        
        Args:
            pdf_path: Path to input PDF file
            output_path: Path for output MP3 file
            language: Language code (optional, uses config default)
            skip_cleaning: Skip LLM text cleaning step
        """
        # Validate paths
        self.validate_paths(pdf_path, output_path)
        
        if self.config.verbose:
            print(f"Extracting text from: {pdf_path}")
        
        # Extract text from PDF
        raw_text = self.extract_text_from_pdf(pdf_path)
        
        if not raw_text:
            raise ValueError("No text found in PDF")
        
        # Save raw text if configured
        if self.config.should_save_raw_text():
            self.save_text_file(raw_text, output_path, 'raw')
        
        # Clean text unless skipped
        if skip_cleaning:
            cleaned_text = raw_text
        else:
            cleaned_text = self.content_cleaner.clean(raw_text)
            
            # Save cleaned text if configured
            if self.config.should_save_cleaned_text():
                self.save_text_file(cleaned_text, output_path, 'cleaned')
        
        # Convert to speech
        self.tts_processor.synthesize(cleaned_text, output_path, language)
        
        if self.config.verbose:
            print("Conversion completed successfully!")