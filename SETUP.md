# PDF to Audio Converter - Setup Guide

## Quick Start

1. **Copy the default configuration:**
   ```bash
   cp default_config.yml config.yml
   ```

2. **Set up your API keys** in `.env` file:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Run conversion:**
   ```bash
   python pdf2audio_new.py --pdf=document.pdf --mp3=output.mp3
   ```

## Configuration

### Basic Setup
The `default_config.yml` contains all settings with detailed comments. 

**Essential settings to customize:**
- `tts.provider`: Choose your TTS engine (`gtts`, `openai`, `aws`)
- `llm.provider`: Choose your text cleaning engine (`openai`, `gemini`)
- `tts.voice`: Configure voice settings for your chosen provider

### API Keys Required

**For Free Usage (Google TTS only):**
- No API keys needed! Uses Google TTS (gtts)

**For Premium TTS (OpenAI/AWS):**
- `OPENAI_API_KEY` - for OpenAI TTS
- `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` - for AWS Polly

**For Text Cleaning (Optional but Recommended):**
- `OPENAI_API_KEY` - for ChatGPT text cleaning
- `GEMINI_API_KEY` - for Google Gemini text cleaning

### Example Configurations

**Budget Setup (Free):**
```yaml
tts:
  provider: "gtts"
llm:
  provider: "openai"  # Still needs OPENAI_API_KEY for text cleaning
```

**High Quality Setup:**
```yaml
tts:
  provider: "openai"
  voice:
    openai:
      voice: "nova"
      model: "tts-1-hd"
llm:
  provider: "openai"
```

**AWS Polly Setup:**
```yaml
tts:
  provider: "aws"
  voice:
    aws:
      voice_id: "Joanna"
      engine: "neural"
```

## Usage Examples

### Command Line
```bash
# Basic conversion
python pdf2audio_new.py --pdf=document.pdf --mp3=output.mp3

# Spanish conversion with specific providers
python pdf2audio_new.py --pdf=documento.pdf --mp3=audio.mp3 --lang=es --ttsprovider=aws --cleaner-llm=gemini

# Skip text cleaning (faster, lower quality)
python pdf2audio_new.py --pdf=document.pdf --mp3=output.mp3 --no-llm
```

### Python API
```python
from config import Config
from processors import PDFProcessor, ContentCleaner, TextToSpeechProcessor

# Initialize with your config
config = Config('config.yml')

# Complete pipeline
processor = PDFProcessor(config)
processor.process('document.pdf', 'output.mp3')

# Individual components
cleaner = ContentCleaner(config)
cleaned_text = cleaner.clean(raw_text)

tts = TextToSpeechProcessor(config)
tts.synthesize(cleaned_text, 'output.mp3', 'en')

# Dynamic provider switching
cleaner.set_provider('gemini')
tts.set_provider('aws')
```

## Troubleshooting

**"Config file not found"**: Copy `default_config.yml` to `config.yml`

**"API key not set"**: Add required API keys to `.env` file

**"TextLengthExceededException"**: The new version automatically handles text chunking

**Voice not working**: Check voice name spelling in your provider's documentation

## LLM Chunking (Context Limits)

Long PDFs can exceed LLM context limits. You can tune chunking behavior:

Config (`~/.pdf2audio/config.yml`):
```yaml
llm:
  chunk_strategy: paragraph_sentence_word  # or sentence_word
  max_chunk_chars: 20000                   # reduce if still too large
```

CLI overrides (when using the `pdf2audio` CLI):
```bash
pdf2audio --pdf document.pdf --mp3 out.mp3 \
  --cleaner-llm openai \
  --llm-chunk-strategy paragraph_sentence_word \
  --llm-chunk-chars 15000
```

## File Structure
```
pdf-audiobook/
├── config.yml              # Your configuration (copy from default_config.yml)
├── default_config.yml       # Default configuration template
├── .env                    # Your API keys (copy from .env.example)
├── pdf2audio_new.py        # New modular script
├── pdf2audio.py           # Original script (still works)
└── [various modules]      # Internal implementation files
```
