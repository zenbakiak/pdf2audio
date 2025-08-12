#!/usr/bin/env python3

from typing import Optional, List
import re
import os
from .config import Config
from .llm_providers import LLMFactory
from .tts_providers import TTSFactory, chunk_text


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

        # Optional pre-cleaning to remove headers/footers, page numbers, and boilerplate
        if self.config.get('llm.preclean', True):
            if self.config.verbose:
                print("Applying pre-cleaning heuristics...")
            text = preclean_text(text,
                                 min_repeats=int(self.config.get('llm.preclean_min_repeats', 3)),
                                 max_line_len=int(self.config.get('llm.preclean_max_line_length', 80)))

        # Chunk text to avoid hitting LLM context limits
        max_chunk_chars = self.config.get('llm.max_chunk_chars', 20000)
        strategy = self.config.get('llm.chunk_strategy', 'paragraph_sentence_word')
        if strategy == 'paragraph_sentence_word':
            pieces = chunk_text_paragraph_sentence_word(text, max_chunk_chars)
        else:
            # Fallback to sentence->word strategy
            pieces = chunk_text(text, max_chunk_chars)

        if self.config.verbose and len(pieces) > 1:
            print(f"Cleaning in {len(pieces)} chunks to respect context limits...")

        cleaned_chunks: List[str] = []
        for i, piece in enumerate(pieces):
            if self.config.verbose and len(pieces) > 1:
                print(f"  - Cleaning chunk {i+1}/{len(pieces)} ({len(piece)} chars)")
            cleaned_chunks.append(self.provider.clean_text(piece))

        return "\n\n".join(cleaned_chunks)

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

        # Chunk to avoid LLM context issues when tagging SSML
        max_chunk_chars = self.config.get('llm.max_chunk_chars', 20000)
        strategy = self.config.get('llm.chunk_strategy', 'paragraph_sentence_word')
        if strategy == 'paragraph_sentence_word':
            pieces = chunk_text_paragraph_sentence_word(text, max_chunk_chars)
        else:
            pieces = chunk_text(text, max_chunk_chars)

        if self.config.verbose and len(pieces) > 1:
            print(f"Applying SSML in {len(pieces)} chunks...")

        ssml_chunks: List[str] = []
        for i, piece in enumerate(pieces):
            if self.config.verbose and len(pieces) > 1:
                print(f"  - SSML chunk {i+1}/{len(pieces)} ({len(piece)} chars)")
            ssml_chunks.append(self.provider.apply_ssml(piece))

        return "\n\n".join(ssml_chunks)
    
    def summarize(self, text: str, target_language: Optional[str] = None) -> str:
        """
        Summarize text into a concise, audiobook-style narrative using the LLM provider.
        Applies pre-cleaning and chunking similar to cleaning, then merges summaries.
        """
        if not text:
            return text

        if self.config.verbose:
            print(f"Summarizing with {self.config.llm_provider}...")

        # Optional pre-cleaning to reduce noise before summarization
        if self.config.get('llm.preclean', True):
            if self.config.verbose:
                print("Applying pre-cleaning heuristics before summarization...")
            text = preclean_text(text,
                                 min_repeats=int(self.config.get('llm.preclean_min_repeats', 3)),
                                 max_line_len=int(self.config.get('llm.preclean_max_line_length', 80)))

        max_chunk_chars = self.config.get('llm.max_chunk_chars', 20000)
        strategy = self.config.get('llm.chunk_strategy', 'paragraph_sentence_word')
        pieces = chunk_text_paragraph_sentence_word(text, max_chunk_chars) if strategy == 'paragraph_sentence_word' else chunk_text(text, max_chunk_chars)

        # Compute target summary length (in words)
        total_words = len(text.split())
        min_ratio = float(self.config.get('llm.min_summary_ratio', 0.45))
        target_words = max(1, int(total_words * min_ratio))

        if self.config.verbose and len(pieces) > 1:
            print(f"Summarizing in {len(pieces)} chunks, then merging...")

        summaries: List[str] = []
        for i, piece in enumerate(pieces):
            if self.config.verbose and len(pieces) > 1:
                print(f"  - Summarizing chunk {i+1}/{len(pieces)} ({len(piece)} chars)")
            # Per-chunk target words proportional to piece size
            piece_words = len(piece.split())
            piece_target = max(1, int(piece_words * min_ratio))
            try:
                summaries.append(self.provider.summarize_text(piece, language=target_language, target_words=piece_target))
            except TypeError:
                # Backward compatibility with providers lacking new parameters
                try:
                    summaries.append(self.provider.summarize_text(piece, language=target_language))
                except TypeError:
                    summaries.append(self.provider.summarize_text(piece))

        if len(summaries) == 1:
            return summaries[0]

        # Merge chunk summaries into a cohesive single summary
        merged_input = "\n\n".join(summaries)
        try:
            merged = self.provider.merge_summaries(merged_input, language=target_language, target_words=target_words)
        except TypeError:
            try:
                merged = self.provider.merge_summaries(merged_input, language=target_language)
            except TypeError:
                merged = self.provider.merge_summaries(merged_input)

        # Ensure minimum length; expand once if too short
        tolerance = float(self.config.get('llm.summary_ratio_tolerance', 0.9))
        if len(merged.split()) < int(target_words * tolerance):
            if self.config.verbose:
                print("Merged summary below target length; expanding...")
            try:
                expanded = self.provider.expand_summary(merged, source=merged_input, language=target_language, target_words=target_words)
            except TypeError:
                try:
                    expanded = self.provider.expand_summary(merged, target_words=target_words)
                except TypeError:
                    expanded = merged
            return expanded

        return merged
    
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
    
    def synthesize(self, chunks: List[str], output_path: str, language: Optional[str] = None) -> None:
        """
        Convert text chunks to speech using the configured TTS provider.
        
        Args:
            chunks: List of text chunks to convert to speech
            output_path: Path where to save the audio file
            language: Language code (optional, uses config default)
        """
        if not chunks:
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
            # Explicitly show TTS model for OpenAI if configured
            if provider_name == 'openai':
                model = voice_config.get('model') if isinstance(voice_config, dict) else None
                if model:
                    print(f"TTS model: {model}")
        
        # Validate speaking rate if it's not 1.0
        speaking_rate = self.config.speaking_rate
        if speaking_rate != 1.0:
            from .tts_providers import validate_speaking_rate
            validate_speaking_rate(speaking_rate)
        
        if self.config.verbose:
            print(f"Converting text to speech (language: {lang_code})")
        
        # Synthesize audio
        self.provider.synthesize(chunks, output_path, lang_code)
        
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
        
        # Always save raw text
        self.save_text_file(raw_text, output_path, 'raw')
        
        # Clean text unless skipped
        if skip_cleaning:
            cleaned_text = raw_text
        else:
            cleaned_text = self.content_cleaner.clean(raw_text)
            
            # Save cleaned text
            self.save_text_file(cleaned_text, output_path, 'cleaned')
        
        # Chunk text and convert to speech
        max_chunk = self.tts_processor.provider.get_max_chunk_size(is_ssml=False)
        chunks = chunk_text(cleaned_text, max_chunk)
        self.tts_processor.synthesize(chunks, output_path, language)
        
        if self.config.verbose:
            print("Conversion completed successfully!")


def chunk_text_paragraph_sentence_word(text: str, max_length: int) -> List[str]:
    """
    Chunk text preferring paragraph boundaries first, then sentences, then words.
    Ensures words are not split unless a single word exceeds max_length.
    """
    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    current = ""

    # Split paragraphs on blank lines
    paragraphs = re.split(r"\n\s*\n+", text)

    def pack_sentence_word(s: str) -> List[str]:
        return chunk_text(s, max_length)

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # If it fits into current chunk, append with paragraph break
        sep = "\n\n" if current else ""
        if current and len(current) + len(sep) + len(para) <= max_length:
            current = f"{current}{sep}{para}"
            continue

        # If paragraph alone fits in an empty chunk
        if len(para) <= max_length and not current:
            current = para
            continue

        # Paragraph too large; split by sentence->word
        pchunks = pack_sentence_word(para)

        if current:
            # Flush current before adding paragraph chunks
            chunks.append(current)
            current = ""

        # Keep the last subchunk open for potential packing with next paragraph
        if len(pchunks) > 1:
            chunks.extend(pchunks[:-1])
            current = pchunks[-1]
        else:
            # Single subchunk already exceeds capacity earlier; set as current
            current = pchunks[0]

    if current:
        chunks.append(current)

    return chunks


def preclean_text(text: str, min_repeats: int = 3, max_line_len: int = 80) -> str:
    """
    Remove common headers/footers and boilerplate before LLM cleaning.
    - Drops short lines that repeat at least `min_repeats` times across the doc.
    - Removes page number patterns like "Page X" or lines that are only digits.
    - Removes standalone URLs.
    Preserves blank lines to keep paragraph boundaries.
    """
    lines = text.splitlines()
    # Count normalized line frequencies
    from collections import Counter
    norm = [ln.strip() for ln in lines]
    freq = Counter([ln for ln in norm if ln])

    out: List[str] = []
    for original, stripped in zip(lines, norm):
        if stripped == "":
            out.append("")
            continue

        # Drop frequent short lines (likely header/footer)
        if len(stripped) <= max_line_len and freq.get(stripped, 0) >= min_repeats:
            continue

        low = stripped.lower()
        # Common page number/footer patterns
        if re.match(r"^(page\s+\d+(\s+of\s+\d+)?)$", low):
            continue
        if re.match(r"^\d+$", stripped):
            continue
        # Standalone URL
        if re.match(r"^https?://\S+$", stripped):
            continue

        out.append(original)

    return "\n".join(out)
