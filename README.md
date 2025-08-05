# pdf2audio, a PDF to Audio (Text To Speech) tool

Convert PDF files to MP3 audio using text-to-speech with AI-powered text cleaning.

## Features

- **PDF Text Extraction** using pdfplumber
- **AI-Powered Text Cleaning** with OpenAI GPT or Google Gemini
- **Multiple TTS Providers** with voice customization:
  - Google TTS (gTTS) - Free, basic voices
  - OpenAI TTS - High quality voices (alloy, echo, fable, onyx, nova, shimmer)
  - AWS Polly - Wide selection of voices and languages
- **Voice Configuration** including gender, accent, and voice selection
- **Configurable Audio Settings** via YAML config
- **Multiple Language Support**

## Installation

### Quick Start (Recommended)

1. **Clone and install the package:**
   ```bash
   git clone https://github.com/zenbakiak/pdf2audio.git
   cd pdf2audio
   pip install -e .
   ```

2. **Test the installation:**
   ```bash
   pdf2audio --help
   ```
   This creates the `~/.pdf2audio/` config directory automatically.

3. **Add your API keys:**
   ```bash
   nano ~/.pdf2audio/.env
   ```
   Add keys for the services you want to use (see [API Keys](#api-keys) section below).

4. **Try it out:**
   ```bash
   pdf2audio --pdf assets/test.pdf --mp3 test.mp3 --no-llm --ttsprovider gtts
   ```

### Installation Options

#### Option 1: Package Installation (Recommended)
```bash
# Development installation (editable)
git clone https://github.com/zenbakiak/pdf2audio.git
cd pdf2audio
pip install -e .

# Or install from PyPI (when published)
pip install pdf2audio
```

After installation, you'll have access to these commands:
- `pdf2audio` - Main command
- `pdf-to-audio` - Alternative command name

#### Option 2: Manual Installation
```bash
git clone https://github.com/zenbakiak/pdf2audio.git
cd pdf2audio
pip install -r requirements.txt
python pdf2audio.py --help
```

## API Keys

### Automatic Configuration (Package Installation)

When you first run `pdf2audio`, it automatically creates `~/.pdf2audio/` with:
- `config.yml` - Main configuration file
- `.env` - Your API keys (edit this file)
- `.env.example` - Template file

### Manual Configuration

For manual installation, copy the environment template:
```bash
cp .env.example .env
```

### Required API Keys

Edit `~/.pdf2audio/.env` (or `.env` for manual installation) and add your API keys:

```bash
# For AI text cleaning (choose one or both)
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# For premium TTS providers (optional)
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
```

**Note:** You can start with just Google TTS (free) by using `--no-llm --ttsprovider gtts` - no API keys needed!

## Usage

### Package Installation Commands

```bash
# Basic usage
pdf2audio --pdf=/path/to/file.pdf --mp3=/path/to/output.mp3 --lang=es_la

# Alternative command name
pdf-to-audio --pdf=/path/to/file.pdf --mp3=/path/to/output.mp3 --lang=es_la
```

### Manual Installation Commands

```bash
python pdf2audio.py --pdf=/path/to/file.pdf --mp3=/path/to/output.mp3 --lang=es_la
```

### Example Usage

```bash
# Try the example file
pdf2audio --pdf=assets/test.pdf --mp3=assets/test.mp3 \
       --no-llm --ttsprovider=gtts --lang=es_la
```



### Parameters

- `--pdf`: Path to input PDF file (required)
- `--mp3`: Path to output MP3 file (required)
- `--lang`: Language code (optional, uses config default)
- `--config`: Path to config file (default: config.yml)
- `--no-llm`: Skip AI text cleaning
- `--cleaner-llm`: LLM provider for text cleaning (openai|gemini) - overrides config
- `--ttsprovider`: TTS provider (gtts|openai|aws|google) - overrides config

### Language Codes

- `en`: English
- `es`: Spanish
- `es_la`: Spanish (Latin America)
- Many other codes supported by Google TTS

## Configuration

Edit `config.yml` to customize:

- **TTS Provider**: Choose between gtts, openai, aws
- **Voice Settings**: Gender, accent, specific voice selection per provider
- **Speaking Rate**: Speed control (0.25-2.0x)
- **LLM Provider**: OpenAI or Gemini for text cleaning
- **Output Options**: Save raw/cleaned text files

### TTS Provider Options

#### Google TTS (Free)
```yaml
tts:
  provider: "gtts"
  # Limited voice options, uses default voice for language
```

#### OpenAI TTS (Premium)
```yaml
tts:
  provider: "openai"
  voice:
    openai:
      voice: "alloy"  # alloy, echo, fable, onyx, nova, shimmer
      model: "tts-1"  # tts-1 or tts-1-hd (higher quality)
```


#### AWS Polly (Premium)
```yaml
tts:
  provider: "aws"
  voice:
    aws:
      voice_id: "Joanna"  # Female
      # voice_id: "Matthew"  # Male
      # voice_id: "Lupe"     # Spanish Female
      engine: "neural"  # standard or neural

#### Google Cloud TTS (Premium)
```yaml
tts:
  provider: "google"
  voice:
    google:
      language_code: "en-US"
      voice_name: "en-US-Studio-M" # Male studio voice
      # Other popular voices:
      # en-US-Studio-O (Female)
      # en-US-Wavenet-D (Male)
      # en-US-Wavenet-F (Female)
```

## Examples

### Using Package Installation

```bash
# Basic conversion with AI cleaning
pdf2audio --pdf=document.pdf --mp3=output.mp3

# Spanish conversion
pdf2audio --pdf=documento.pdf --mp3=audio.mp3 --lang=es_la

# Skip AI cleaning
pdf2audio --pdf=document.pdf --mp3=output.mp3 --no-llm

# Use specific providers (overrides config)
pdf2audio --pdf=document.pdf --mp3=output.mp3 --cleaner-llm=gemini --ttsprovider=openai

# Use OpenAI for both text cleaning and TTS
pdf2audio --pdf=document.pdf --mp3=output.mp3 --cleaner-llm=openai --ttsprovider=openai

# Use free options only
pdf2audio --pdf=document.pdf --mp3=output.mp3 --ttsprovider=gtts --no-llm

# Custom config file
pdf2audio --pdf=document.pdf --mp3=output.mp3 --config=my-config.yml
```

### Using Manual Installation

```bash
# Basic conversion with AI cleaning
python pdf2audio.py --pdf=document.pdf --mp3=output.mp3

# Spanish conversion
python pdf2audio.py --pdf=documento.pdf --mp3=audio.mp3 --lang=es_la

# Skip AI cleaning
python pdf2audio.py --pdf=document.pdf --mp3=output.mp3 --no-llm

# Use specific providers (overrides config)
python pdf2audio.py --pdf=document.pdf --mp3=output.mp3 --cleaner-llm=gemini --ttsprovider=openai

# Use OpenAI for both text cleaning and TTS
python pdf2audio.py --pdf=document.pdf --mp3=output.mp3 --cleaner-llm=openai --ttsprovider=openai

# Use free options only
python pdf2audio.py --pdf=document.pdf --mp3=output.mp3 --ttsprovider=gtts --no-llm

# Custom config file
python pdf2audio.py --pdf=document.pdf --mp3=output.mp3 --config=my-config.yml
```

## Troubleshooting

### Installation Issues

**ImportError or ModuleNotFoundError:**
```bash
# Reinstall the package
pip uninstall pdf2audio
pip install -e .
```

**Permission errors:**
```bash
# Install with user permissions
pip install -e . --user
```

**Command not found:**
```bash
# Verify installation
pip list | grep pdf2audio

# Try full path
python -m pdf2audio.cli --help
```

### Configuration Issues

**Config directory not created:**
```bash
# Manually create and test
mkdir -p ~/.pdf2audio
pdf2audio --help
```

**API key errors:**
```bash
# Check your .env file has no extra spaces
cat ~/.pdf2audio/.env

# Test with free options first
pdf2audio --pdf test.pdf --mp3 test.mp3 --no-llm --ttsprovider gtts
```

**"No text found in PDF" error:**
- Try a different PDF file
- Ensure the PDF contains selectable text (not just images)
- Use `--verbose` flag for more details

### Getting Help

- Check the [Installation Guide](INSTALL.md) for detailed setup
- Report issues at: https://github.com/zenbakiak/pdf2audio/issues
- Use `--verbose` flag for detailed error messages

## TTS Provider Documentation

### Complete Voice and Language Support

#### Google Text-to-Speech (gTTS) - Free Option

**Languages Supported (104 total):**
- Major languages: English (`en`), Spanish (`es`), French (`fr`), German (`de`), Italian (`it`), Portuguese (`pt`), Russian (`ru`), Chinese (`zh`), Japanese (`ja`), Korean (`ko`), Arabic (`ar`), Hindi (`hi`)
- Regional variants: French Canada (`fr-CA`), Portuguese Portugal (`pt-PT`), Chinese Taiwan (`zh-TW`)
- Complete list includes: Afrikaans, Albanian, Amharic, Bengali, Bosnian, Bulgarian, Catalan, Croatian, Czech, Danish, Dutch, Estonian, Finnish, Galician, Greek, Gujarati, Hausa, Hebrew, Hungarian, Icelandic, Indonesian, Javanese, Kannada, Khmer, Latin, Latvian, Lithuanian, Malayalam, Marathi, Malay, Myanmar, Nepali, Norwegian, Polish, Punjabi, Romanian, Serbian, Sinhala, Slovak, Sundanese, Swahili, Swedish, Tamil, Telugu, Thai, Filipino, Turkish, Ukrainian, Urdu, Vietnamese, Welsh, and more

**Voice Features:**
- Single voice per language (no customization)
- Fixed gender per language
- Standard quality audio
- Speed control: slow/normal only

**Limitations:**
- Requires internet connection
- 5000 character limit per request
- No neural or premium voices

---

#### OpenAI TTS - Premium Option

**Available Voices (6 total):**
- `alloy`: Neutral, versatile voice
- `echo`: Male voice
- `fable`: Male voice
- `onyx`: Male voice
- `nova`: Female voice
- `shimmer`: Female voice

**Language Support:**
- **Multilingual**: All voices support 50+ languages including English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi
- **Automatic Language Detection**: Voices adapt pronunciation based on text language
- **Cross-lingual Capability**: Single voice can speak multiple languages naturally

**Advanced Features:**
- Neural voice synthesis with HD quality option
- Speed control: 0.25x to 4.0x
- Multiple audio formats: MP3, Opus, AAC, FLAC, WAV, PCM
- Real-time streaming support
- 4096 character limit per request

---

#### AWS Polly - Premium Option

**Four Voice Engines:**

1. **Generative Engine (Latest)**: 5 most human-like voices for conversational AI
2. **Neural Engine**: 36 language variants with high-quality synthesis
3. **Long-form Engine**: 13 expressive voices optimized for long content
4. **Standard Engine**: 60 voices (cost-effective option)

**Voice Examples by Language:**
- **English (US)**: Joanna, Matthew, Kendra, Joey, Salli, Danielle, Kevin, Gregory, Justin, Kimberly
- **Spanish (Spain)**: Conchita, Lucia, Enrique, Sergio
- **Spanish (Mexico)**: Mia, Andrés
- **Spanish (US)**: Lupe, Penélope, Miguel, Pedro
- **French**: Céline, Mathieu, Léa
- **German**: Marlene, Hans, Vicki
- **Italian**: Carla, Giorgio, Bianca
- **Portuguese**: Inês, Cristiano, Vitória
- **Japanese**: Mizuki, Takumi
- **Korean**: Seoyeon

**Special Features:**
- **Bilingual Voices**: Some voices support multiple languages
- **Speaking Styles**: Newscaster style for select voices
- **Voice Conversion**: Transform one voice to another
- **SSML Support**: Advanced markup for pronunciation control
- **Multiple Formats**: MP3, OGG, PCM with various sampling rates

---

### Provider Comparison

| Feature | gTTS (Free) | OpenAI TTS | AWS Polly |
|---------|-------------|------------|-----------|
| **Languages** | 104 | 50+ (multilingual) | 40+ languages |
| **Total Voices** | 1 per language | 6 premium | 100+ total |
| **Voice Quality** | Standard | Neural HD | 4 engine types |
| **Cost** | Free | Premium | Freemium |
| **Customization** | None | Limited | Moderate |
| **Real-time** | No | Yes | Yes |
| **Best For** | Basic apps | Conversational AI | Diverse needs |

### Recommendations by Use Case

- **Budget-conscious projects**: Use gTTS for basic functionality
- **Conversational AI/Chatbots**: OpenAI TTS for natural dialogue
- **AWS ecosystem/Flexible requirements**: AWS Polly for diverse voice options

## Output Files

The script can generate:
- `output.mp3`: The audio file
- `output_raw.txt`: Original extracted text (if enabled in config)
- `output_cleaned.txt`: AI-cleaned text (if enabled in config)