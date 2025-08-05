#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from .config import Config
from .processors import PDFProcessor, ContentCleaner, TextToSpeechProcessor
from .tts_providers import chunk_text


def load_environment():
    """Load environment variables from ~/.pdf2audio/.env"""
    user_config_dir = Path.home() / ".pdf2audio"
    env_file = user_config_dir / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Try current directory as fallback
        if Path(".env").exists():
            load_dotenv(".env")


def create_argument_parser():
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert PDF files to MP3 audio with AI-powered text cleaning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pdf2audio --pdf document.pdf --mp3 output.mp3
  pdf2audio --pdf document.pdf --mp3 output.mp3 --lang es_la
  pdf2audio --pdf document.pdf --mp3 output.mp3 --no-llm
  pdf2audio --pdf document.pdf --mp3 output.mp3 --cleaner-llm gemini --ttsprovider aws
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--pdf', 
        required=True,
        help='Path to input PDF file'
    )
    parser.add_argument(
        '--mp3', 
        required=True,
        help='Path to output MP3 file'
    )
    
    # Optional arguments
    parser.add_argument(
        '--lang',
        help='Language code for TTS (e.g., en, es, es_la). Uses config default if not specified'
    )
    parser.add_argument(
        '--config',
        help='Path to custom config file (default: ~/.pdf2audio/config.yml)'
    )
    parser.add_argument(
        '--no-llm',
        action='store_true',
        help='Skip AI text cleaning'
    )
    parser.add_argument(
        '--cleaner-llm',
        choices=['openai', 'gemini'],
        help='LLM provider for text cleaning (overrides config)'
    )
    parser.add_argument(
        '--ttsprovider',
        choices=['gtts', 'openai', 'aws', 'google'],
        help='TTS provider (overrides config)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--use-ssml',
        action='store_true',
        help='Enable SSML for TTS'
    )
    parser.add_argument(
        '--save-chunks',
        action='store_true',
        help='Save cleaned text chunks to files'
    )
    
    return parser


def validate_arguments(args):
    """Validate command line arguments."""
    # Check if PDF file exists
    if not Path(args.pdf).exists():
        print(f"Error: PDF file not found: {args.pdf}")
        return False
    
    # Ensure output directory exists
    output_path = Path(args.mp3)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    return True


def main():
    """Main CLI entry point."""
    # Load environment variables
    load_environment()
    
    # Parse arguments
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Validate arguments
    if not validate_arguments(args):
        sys.exit(1)
    
    try:
        # Initialize configuration
        config = Config(args.config)
        
        # Override config with CLI arguments if provided
        if args.cleaner_llm:
            config.set('llm.provider', args.cleaner_llm)
        
        if args.ttsprovider:
            config.set('tts.provider', args.ttsprovider)
        
        if args.lang:
            # Map language code if needed
            mapped_lang = config.get_language_mapping(args.lang)
            config.set('tts.default_language', mapped_lang)
        
        if args.verbose:
            config.set('output.verbose', True)

        if args.use_ssml:
            config.set('llm.use_ssml', True)
        
        if args.save_chunks:
            config.set('output.save_cleaned_chunks', True)
        
        # Initialize processors
        pdf_processor = PDFProcessor(config)
        content_cleaner = ContentCleaner(config) if not args.no_llm else None
        tts_processor = TextToSpeechProcessor(config)
        
        # Process PDF
        print(f"Extracting text from: {args.pdf}")
        text = pdf_processor.extract_text_from_pdf(args.pdf)
        
        if not text.strip():
            print("Error: No text found in PDF")
            sys.exit(1)
        
        # Save raw text if configured
        if config.should_save_raw_text():
            raw_output_path = Path(args.mp3.replace('.mp3', '_raw.txt'))
            with open(raw_output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Raw text saved to: {raw_output_path}")
        
        # Clean text if LLM is enabled
        if content_cleaner:
            print(f"Cleaning text with {config.llm_provider}...")
            cleaned_text = content_cleaner.clean(text)
        else:
            print("Skipping text cleaning (--no-llm)")
            cleaned_text = text
        
        # Save cleaned text if configured
        if config.should_save_cleaned_text() and content_cleaner:
            cleaned_output_path = Path(args.mp3.replace('.mp3', '_cleaned.txt'))
            with open(cleaned_output_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_text)
            print(f"Cleaned text saved to: {cleaned_output_path}")

        # Chunk the text
        max_chunk_size = tts_processor.provider.get_max_chunk_size(is_ssml=args.use_ssml)
        chunks = chunk_text(cleaned_text, max_chunk_size)
        
        # Save cleaned chunks if configured
        if config.should_save_cleaned_chunks():
            for i, chunk in enumerate(chunks):
                chunk_path = Path(args.mp3.replace('.mp3', f'_cleaned_chunk_{i}.txt'))
                with open(chunk_path, 'w', encoding='utf-8') as f:
                    f.write(chunk)
            print(f"Saved {len(chunks)} cleaned chunks.")

        # Apply SSML if enabled
        if args.use_ssml:
            if not content_cleaner:
                print("Warning: --use-ssml requires an LLM cleaner. Skipping SSML.")
                final_chunks = chunks
            else:
                print(f"Applying SSML to {len(chunks)} chunks...")
                final_chunks = [content_cleaner.apply_ssml(chunk) for chunk in chunks]
                # Save SSML text if configured
                if config.should_save_cleaned_text():
                    ssml_output_path = Path(args.mp3.replace('.mp3', '_ssml.txt'))
                    with open(ssml_output_path, 'w', encoding='utf-8') as f:
                        f.write("\n\n---\n\n".join(final_chunks))
                    print(f"SSML text saved to: {ssml_output_path}")
        else:
            final_chunks = chunks
        
        # Convert to speech
        print(f"Converting to speech with {config.tts_provider}...")
        language = config.get('tts.default_language', 'en')
        tts_processor.synthesize(final_chunks, args.mp3, language)
        
        print(f"✅ Audio file created: {args.mp3}")
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose or config.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()