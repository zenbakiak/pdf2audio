#!/usr/bin/env python3

import argparse
import sys
from dotenv import load_dotenv
from config import Config
from processors import PDFProcessor, ContentCleaner, TextToSpeechProcessor


def main():
    """Main entry point for PDF to audio conversion."""
    # Load environment variables from .env file
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert PDF to audio using text-to-speech')
    parser.add_argument('--pdf', required=True, help='Path to input PDF file')
    parser.add_argument('--mp3', required=True, help='Path to output MP3 file')
    parser.add_argument('--lang', help='Language code (e.g., en, es, es-mx, es-la)')
    parser.add_argument('--config', default='config.yml', help='Path to config file')
    parser.add_argument('--no-llm', action='store_true', help='Skip LLM text cleaning')
    parser.add_argument('--cleaner-llm', choices=['openai', 'gemini'],
                       help='LLM provider for text cleaning (overrides config)')
    parser.add_argument('--ttsprovider', choices=['gtts', 'openai', 'aws'],
                       help='TTS provider (overrides config)')

    args = parser.parse_args()

    try:
        # Initialize configuration
        config = Config(args.config)

        # Override config with CLI parameters
        if args.cleaner_llm:
            config.set('llm.provider', args.cleaner_llm)
            if config.verbose:
                print(f"Overriding LLM provider with CLI parameter: {args.cleaner_llm}")

        if args.ttsprovider:
            config.set('tts.provider', args.ttsprovider)
            if config.verbose:
                print(f"Overriding TTS provider with CLI parameter: {args.ttsprovider}")

        # Show configuration info
        if config.verbose:
            print(f"Using config: {args.config}")
            print(f"LLM Provider: {config.llm_provider}")
            print(f"TTS Provider: {config.tts_provider}")

        # Initialize processor and run conversion
        processor = PDFProcessor(config)
        processor.process(
            pdf_path=args.pdf,
            output_path=args.mp3,
            language=args.lang,
            skip_cleaning=args.no_llm
        )

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def demo_api():
    """Demonstrate the new API usage."""
    load_dotenv()

    # Simple usage examples
    config = Config()

    # Example 1: Clean content
    content_cleaner = ContentCleaner(config)
    raw_text = "This is some messy   text\nwith\nweird formatting."
    cleaned_text = content_cleaner.clean(raw_text)
    print("Cleaned text:", cleaned_text)

    # Example 2: Text to speech
    tts_processor = TextToSpeechProcessor(config)
    tts_processor.synthesize("Hello world", "test_output.mp3", "en")

    # Example 3: Switch providers dynamically
    content_cleaner.set_provider('gemini')  # Switch to Gemini
    tts_processor.set_provider('openai')    # Switch to OpenAI TTS

    # Example 4: Complete PDF processing
    pdf_processor = PDFProcessor(config)
    pdf_processor.process("document.pdf", "output.mp3", language="es")


if __name__ == "__main__":
    main()