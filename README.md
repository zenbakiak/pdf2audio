# pdf2audio: PDF to Audiobook Converter

Convert PDF files to high-quality MP3 audiobooks using Text-to-Speech (TTS) and AI-powered text cleaning.

## Features

- **PDF Text Extraction**: Uses `pdfplumber` to accurately extract text from PDF files.
- **AI-Powered Text Cleaning**: Leverages Large Language Models (LLMs) like OpenAI GPT or Google Gemini to clean and format text for natural-sounding speech.
- **Multiple TTS Providers**:
  - **Google TTS (gTTS)**: Free, basic voices for quick conversions.
  - **OpenAI TTS**: High-quality, natural-sounding voices.
  - **AWS Polly**: A wide selection of voices and languages with neural and standard engines.
  - **Google Cloud TTS**: Premium voices with multiple tiers, including standard, WaveNet, and studio-quality options.
- **SSML Support**: Use Speech Synthesis Markup Language (SSML) for fine-grained control over pronunciation, intonation, and pacing (supported by AWS Polly and Google Cloud TTS).
- **Customizable Configuration**: Fine-tune voice, language, speaking rate, and other settings via a simple YAML file.
- **Command-Line Interface**: Easy-to-use CLI for batch processing and automation.

## Installation

### Quick Start (Recommended)

1.  **Clone the repository and install in "editable" mode:**
    ```bash
    git clone https://github.com/zenbakiak/pdf2audio.git
    cd pdf2audio
    pip install -e .
    ```
    This method ensures that any changes you make to the source code are immediately available.

2.  **Run the CLI to initialize configuration:**
    ```bash
    pdf2audio --help
    ```
    This command will create the `~/.pdf2audio/` directory, which contains your configuration files.

3.  **Add your API keys:**
    Open the `.env` file to add your API keys for the services you plan to use.
    ```bash
    nano ~/.pdf2audio/.env
    ```

4.  **Test the installation with a free provider:**
    ```bash
    pdf2audio --pdf assets/test.pdf --mp3 test.mp3 --no-llm --ttsprovider gtts
    ```

### Production Installation

Once the package is published to PyPI, you can install it directly:
```bash
pip install pdf2audio
```

## Configuration

### API Keys

On the first run, `pdf2audio` creates a `~/.pdf2audio/.env` file for your API keys. You'll need to add the following keys for the services you want to use:

```bash
# For AI-powered text cleaning (choose one or both)
OPENAI_API_KEY="your_openai_api_key"
GEMINI_API_KEY="your_gemini_api_key"

# For premium TTS providers
AWS_ACCESS_KEY_ID="your_aws_access_key"
AWS_SECRET_ACCESS_KEY="your_aws_secret_key"

# For Google Cloud TTS
# Path to your Google Cloud service account key file
GOOGLE_APPLICATION_CREDENTIALS="~/.config/gcloud/application_default_credentials.json"
```

**Note**: You can start without any API keys by using the free Google TTS provider: `--no-llm --ttsprovider gtts`.

### Configuration File

Customize the behavior of `pdf2audio` by editing `~/.pdf2audio/config.yml`. Here, you can set the default TTS and LLM providers, voice settings, speaking rate, and more.

### TTS Provider Options

#### Google TTS (gTTS) - Free
Basic, standard-quality voices. No configuration needed.
```yaml
tts:
  provider: "gtts"
```

#### OpenAI TTS - Premium
High-quality, natural-sounding voices.
```yaml
tts:
  provider: "openai"
  voice:
    openai:
      voice: "alloy"  # alloy, echo, fable, onyx, nova, shimmer
      model: "tts-1-hd" # tts-1 or tts-1-hd (higher quality)
```

#### AWS Polly - Premium
Wide range of voices and languages. Supports SSML.
```yaml
tts:
  provider: "aws"
  voice:
    aws:
      voice_id: "Joanna" # Example voice
      engine: "neural"
```
For a full list of available voices, see the [AWS Polly documentation](https://docs.aws.amazon.com/polly/latest/dg/voicelist.html).

#### Google Cloud TTS - Premium
Studio-quality voices with advanced options. Supports SSML.
```yaml
tts:
  provider: "google"
  voice:
    google:
      language_code: "en-US"
      voice_name: "en-US-Studio-M"
```
For a full list of available voices, see the [Google Cloud TTS documentation](https://cloud.google.com/text-to-speech/docs/voices).

### SSML Support

For advanced control over speech synthesis, you can use SSML. This feature is supported by the `aws` and `google` TTS providers.

To use SSML, enable it in your `config.yml`:
```yaml
llm:
  use_ssml: true
```
The AI will automatically add SSML tags to the cleaned text to improve prosody, pacing, and emphasis. You can also use the `--use-ssml` flag to enable it from the command line.

## Usage

### Command-Line Interface

The primary way to use `pdf2audio` is through its CLI.

```bash
# Basic usage with default settings from config.yml
pdf2audio --pdf /path/to/document.pdf --mp3 /path/to/output.mp3

# Override default language
pdf2audio --pdf document.pdf --mp3 audio.mp3 --lang es_la

# Specify TTS and LLM providers
pdf2audio --pdf document.pdf --mp3 audio.mp3 --ttsprovider openai --cleaner-llm gemini

# Use SSML for advanced synthesis (with a supported provider)
pdf2audio --pdf document.pdf --mp3 audio.mp3 --ttsprovider google --use-ssml

# Skip AI text cleaning for a faster conversion
pdf2audio --pdf document.pdf --mp3 output.mp3 --no-llm
```

### Available Parameters

- `--pdf`: Path to the input PDF file (required).
- `--mp3`: Path to the output MP3 file (required).
- `--lang`: Language code (e.g., `en`, `es_la`). Overrides the default in `config.yml`.
- `--config`: Path to a custom configuration file.
- `--no-llm`: Skip the AI text cleaning step.
- `--cleaner-llm`: Specify the LLM provider for text cleaning (`openai` or `gemini`).
- `--ttsprovider`: Specify the TTS provider (`gtts`, `openai`, `aws`, `google`).
- `--use-ssml`: Enable SSML for advanced speech synthesis (only for `aws` and `google` providers).
- `--verbose`: Enable detailed logging.

## Troubleshooting

- **`ImportError` or `ModuleNotFoundError`**: Your installation may be corrupted. Try reinstalling with `pip install -e .`.
- **Permission Errors**: If you encounter permission issues during installation, try installing with user permissions: `pip install -e . --user`.
- **API Key Errors**: Ensure your API keys are correctly set in `~/.pdf2audio/.env` with no extra spaces or quotes. Test with the free provider (`--no-llm --ttsprovider gtts`) to confirm the rest of your setup is working.
- **"No text found in PDF"**: The PDF may contain images of text instead of selectable text. Try a different PDF file.

For further assistance, please [open an issue](https://github.com/zenbakiak/pdf2audio/issues) on GitHub.

# Author

[zenbakiak](https://github.com/zenbakiak)