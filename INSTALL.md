# PDF2Audio Installation Guide

## Quick Start

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Run the CLI (first time setup):**
   ```bash
   pdf2audio --help
   ```
   This will create `~/.pdf2audio/` directory with configuration files.

3. **Configure API keys:**
   ```bash
   nano ~/.pdf2audio/.env
   ```
   Add your API keys for the services you want to use.

4. **Test with example:**
   ```bash
   pdf2audio --pdf assets/test.pdf --mp3 test.mp3 --no-llm --ttsprovider gtts
   ```

## Detailed Installation Options

### Option 1: Development Installation

```bash
git clone https://github.com/zenbakiak/pdf2audio.git
cd pdf2audio
pip install -e .
```

This installs the package in "editable" mode, meaning changes to the source code are immediately reflected.

### Option 2: Production Installation (when published to PyPI)

```bash
pip install pdf2audio
```

### Option 3: Manual Installation

```bash
pip install -r requirements.txt
python pdf2audio.py --help
```

## Configuration

### Automatic Setup

On first run, the CLI automatically creates:
- `~/.pdf2audio/config.yml` - Main configuration file
- `~/.pdf2audio/.env` - Environment variables for API keys
- `~/.pdf2audio/.env.example` - Template file

### Manual Configuration

1. **Edit configuration:**
   ```bash
   nano ~/.pdf2audio/config.yml
   ```

2. **Add API keys:**
   ```bash
   nano ~/.pdf2audio/.env
   ```

3. **Required environment variables:**
   ```bash
   # For LLM text cleaning
   OPENAI_API_KEY=your_key_here
   GEMINI_API_KEY=your_key_here
   
   # For premium TTS
   AWS_ACCESS_KEY_ID=your_key_here
   AWS_SECRET_ACCESS_KEY=your_key_here
   ```

## Available Commands

After installation, you can use either command:

- `pdf2audio` - Main command
- `pdf-to-audio` - Alternative command name

## Testing Installation

```bash
# Test CLI help
pdf2audio --help

# Test with free providers (no API keys needed)
pdf2audio --pdf assets/test.pdf --mp3 test.mp3 --no-llm --ttsprovider gtts

# Test with OpenAI (requires API key)
pdf2audio --pdf assets/test.pdf --mp3 test.mp3 --cleaner-llm openai --ttsprovider openai
```

## Troubleshooting

### ImportError or ModuleNotFoundError

```bash
# Reinstall in development mode
pip uninstall pdf2audio
pip install -e .
```

### Permission Issues

```bash
# Install with user permissions
pip install -e . --user
```

### Configuration Issues

```bash
# Reset configuration directory
rm -rf ~/.pdf2audio
pdf2audio --help  # This will recreate the directory
```

### API Key Issues

1. Check that your API keys are set in `~/.pdf2audio/.env`
2. Ensure there are no extra spaces or quotes around the keys
3. Test with free providers first: `--no-llm --ttsprovider gtts`

## Uninstallation

```bash
pip uninstall pdf2audio
rm -rf ~/.pdf2audio  # Optional: remove config directory
```