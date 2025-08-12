#!/usr/bin/env python3

import argparse
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import yaml

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
    
    # Input/Output arguments
    parser.add_argument('--pdf', help='Path to input PDF file')
    parser.add_argument('--mp3', help='Path to output MP3 file')
    parser.add_argument('--job', help='Path to a job YAML file to resume/reprocess')
    
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
    # Chunks are always saved; flag removed
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Extract and chunk only; skip LLM and TTS'
    )
    parser.add_argument(
        '--summarize',
        action='store_true',
        help='Generate an audiobook-style summary (requires --cleaner-llm)'
    )
    parser.add_argument(
        '--summary-lang',
        help='Language to use for the summary text (defaults to --lang or config language)'
    )
    parser.add_argument(
        '--llm-chunk-strategy',
        choices=['paragraph_sentence_word', 'sentence_word'],
        help='Chunking strategy for LLM cleaning/SSML (overrides config)'
    )
    parser.add_argument(
        '--llm-chunk-chars',
        type=int,
        help='Max characters per chunk for LLM cleaning/SSML (overrides config)'
    )
    
    return parser


def validate_arguments(args):
    """Validate command line arguments."""
    if not args.job:
        # Require pdf and mp3 when not resuming from a job
        if not args.pdf or not args.mp3:
            print("Error: --pdf and --mp3 are required unless --job is provided.")
            return False
        if not Path(args.pdf).exists():
            print(f"Error: PDF file not found: {args.pdf}")
            return False
        output_path = Path(args.mp3)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        if not Path(args.job).exists():
            print(f"Error: Job file not found: {args.job}")
            return False
    
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
    # Enforce summarize requirements
    if '--summarize' in sys.argv and args.summarize:
        if args.no_llm:
            print("Error: --summarize cannot be used with --no-llm. It requires an LLM.")
            sys.exit(1)
        if not args.cleaner_llm:
            print("Error: --summarize requires --cleaner-llm to specify the LLM provider (e.g., openai or gemini).")
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
        
        if args.llm_chunk_strategy:
            config.set('llm.chunk_strategy', args.llm_chunk_strategy)

        if args.llm_chunk_chars:
            config.set('llm.max_chunk_chars', int(args.llm_chunk_chars))

        if args.dry_run:
            # Force skip LLM and SSML in dry-run mode
            args.no_llm = True
            args.use_ssml = False
            if config.verbose:
                print("Dry run: skipping LLM and TTS; will extract and chunk only.")
        
        # Initialize processors
        pdf_processor = PDFProcessor(config)
        content_cleaner = ContentCleaner(config) if not args.no_llm else None
        tts_processor = TextToSpeechProcessor(config)

        # Guard: disable SSML for providers that don't support it
        if args.use_ssml and config.tts_provider not in ("aws", "google"):
            print(f"Warning: SSML is not supported by provider '{config.tts_provider}'. Disabling SSML.")
            args.use_ssml = False
        
        # Load job file if provided
        job_data = None
        if args.job:
            with open(args.job, 'r', encoding='utf-8') as jf:
                job_data = yaml.safe_load(jf) or {}
            # Populate missing CLI IO from job
            if not args.mp3:
                args.mp3 = job_data.get('outputs', {}).get('mp3')
            if not args.pdf:
                args.pdf = job_data.get('inputs', {}).get('pdf')

        # Compute output paths and organized artifact directories
        output_mp3_path = Path(args.mp3)
        output_base_dir = output_mp3_path.parent
        output_stem = output_mp3_path.stem
        artifact_dir = output_base_dir / output_stem
        chunks_dir = artifact_dir / f"{output_stem}_chunks"

        # Create artifact directories (artifacts always saved)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        # Source text: from job raw_text if provided and exists, else extract
        raw_output_path = artifact_dir / f"{output_stem}_raw.txt"
        text = None
        if job_data and job_data.get('artifacts', {}).get('raw_text') and Path(job_data['artifacts']['raw_text']).exists():
            with open(job_data['artifacts']['raw_text'], 'r', encoding='utf-8') as f:
                text = f.read()
            if config.verbose:
                print(f"Loaded raw text from job: {job_data['artifacts']['raw_text']}")
        else:
            print(f"Extracting text from: {args.pdf}")
            text = pdf_processor.extract_text_from_pdf(args.pdf)
            # Always save raw text
            with open(raw_output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Raw text saved to: {raw_output_path}")
        
        if not text.strip():
            print("Error: No text found in PDF")
            sys.exit(1)
        
        # Determine summary language (if summarizing)
        summary_lang = None
        if args.summarize:
            # Prefer explicit --summary-lang, else use --lang, else config default
            summary_lang = args.summary_lang or args.lang or config.get('tts.default_language', 'en')

        # Clean or summarize text if LLM is enabled (unless dry-run)
        if content_cleaner:
            if args.summarize:
                print(f"Summarizing text with {config.llm_provider}...")
                processed_text = content_cleaner.summarize(text, target_language=summary_lang)
            else:
                print(f"Cleaning text with {config.llm_provider}...")
                processed_text = content_cleaner.clean(text)
        else:
            # If job has cleaned or summary text, reuse it; otherwise proceed with raw
            job_art = job_data.get('artifacts', {}) if job_data else {}
            candidate = job_art.get('cleaned_text') or job_art.get('summary_text')
            if candidate and Path(candidate).exists():
                with open(candidate, 'r', encoding='utf-8') as f:
                    processed_text = f.read()
                print("Loaded processed text from job (skipping LLM)")
            else:
                print("Skipping text cleaning (--no-llm or --dry-run)")
                processed_text = text
        
        # Save processed text if LLM was used
        processed_output_path = None
        if content_cleaner:
            processed_output_path = artifact_dir / (f"{output_stem}_summary.txt" if args.summarize else f"{output_stem}_cleaned.txt")
            with open(processed_output_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            print(f"Processed text saved to: {processed_output_path}")

        # Chunk the text
        max_chunk_size = tts_processor.provider.get_max_chunk_size(is_ssml=args.use_ssml)
        chunks = chunk_text(processed_text, max_chunk_size)
        
        # Always save chunks
        chunks_dir.mkdir(parents=True, exist_ok=True)
        chunk_files = []
        for i, chunk in enumerate(chunks):
            chunk_path = chunks_dir / f"chunk_{i}.txt"
            with open(chunk_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
            chunk_files.append(str(chunk_path))
        print(f"Saved {len(chunks)} chunks to: {chunks_dir}")

        # Apply SSML if enabled (not in dry-run)
        if args.use_ssml:
            if not content_cleaner:
                print("Warning: --use-ssml requires an LLM cleaner. Skipping SSML.")
                final_chunks = chunks
            else:
                print(f"Applying SSML to {len(chunks)} chunks...")
                final_chunks = [content_cleaner.apply_ssml(chunk) for chunk in chunks]
                # Save SSML text
                ssml_output_path = artifact_dir / f"{output_stem}_ssml.txt"
                with open(ssml_output_path, 'w', encoding='utf-8') as f:
                    f.write("\n\n---\n\n".join(final_chunks))
                print(f"SSML text saved to: {ssml_output_path}")
        else:
            final_chunks = chunks
        
        # If dry-run, stop after chunking
        if args.dry_run:
            print(f"Dry run complete. Extracted {len(text)} chars, {len(chunks)} chunks.")
            print(f"Chunks saved to: {chunks_dir}")
            # Write job manifest
            job_path = output_mp3_path.with_suffix('.yml')
            job_manifest = {
                'inputs': {'pdf': args.pdf},
                'outputs': {'mp3': str(output_mp3_path)},
                'params': {
                    'lang': config.get('tts.default_language', 'en'),
                    'tts_provider': config.tts_provider,
                    'llm_provider': None if not content_cleaner else config.llm_provider,
                    'use_ssml': bool(args.use_ssml),
                    'summarize': bool(args.summarize),
                    'llm': {
                        'chunk_strategy': config.get('llm.chunk_strategy', 'paragraph_sentence_word'),
                        'max_chunk_chars': config.get('llm.max_chunk_chars', 20000)
                    }
                },
                'artifacts': {
                    'artifact_dir': str(artifact_dir),
                    'raw_text': str(raw_output_path),
                    'cleaned_text': str(processed_output_path) if (processed_output_path and not args.summarize) else None,
                    'summary_text': str(processed_output_path) if (processed_output_path and args.summarize) else None,
                    'ssml_text': str(artifact_dir / f"{output_stem}_ssml.txt") if args.use_ssml and content_cleaner else None,
                    'chunks_dir': str(chunks_dir),
                    'chunks': chunk_files,
                }
            }
            with open(job_path, 'w', encoding='utf-8') as jf:
                yaml.safe_dump(job_manifest, jf, sort_keys=False, allow_unicode=True)
            print(f"Job manifest saved to: {job_path}")
            return
        
        # Convert to speech
        print(f"Converting to speech with {config.tts_provider}...")
        language = config.get('tts.default_language', 'en')
        tts_processor.synthesize(final_chunks, args.mp3, language)
        
        print(f"✅ Audio file created: {args.mp3}")

        # Write job manifest
        job_path = output_mp3_path.with_suffix('.yml')
        job_manifest = {
            'inputs': {'pdf': args.pdf},
            'outputs': {'mp3': str(output_mp3_path)},
            'params': {
                'lang': config.get('tts.default_language', 'en'),
                'tts_provider': config.tts_provider,
                'llm_provider': None if not content_cleaner else config.llm_provider,
                'use_ssml': bool(args.use_ssml),
                'summarize': bool(args.summarize),
                'llm': {
                    'chunk_strategy': config.get('llm.chunk_strategy', 'paragraph_sentence_word'),
                    'max_chunk_chars': config.get('llm.max_chunk_chars', 20000)
                }
            },
            'artifacts': {
                'artifact_dir': str(artifact_dir),
                'raw_text': str(raw_output_path),
                'cleaned_text': str(processed_output_path) if (processed_output_path and not args.summarize) else None,
                'summary_text': str(processed_output_path) if (processed_output_path and args.summarize) else None,
                'ssml_text': str(artifact_dir / f"{output_stem}_ssml.txt") if args.use_ssml and content_cleaner else None,
                'chunks_dir': str(chunks_dir),
                'chunks': chunk_files,
            }
        }
        with open(job_path, 'w', encoding='utf-8') as jf:
            yaml.safe_dump(job_manifest, jf, sort_keys=False, allow_unicode=True)
        print(f"🗂️  Job manifest saved to: {job_path}")
        
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
