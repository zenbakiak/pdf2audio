# Repository Guidelines

## Project Structure & Module Organization
- `pdf2audio/`: library code
  - `cli.py`: command-line entry; argument parsing and orchestration
  - `processors.py`: PDF extraction, LLM cleaning, and TTS coordination
  - `tts_providers.py`: gTTS, OpenAI, AWS Polly, Google Cloud TTS
  - `llm_providers.py`: OpenAI and Gemini cleaners
  - `config.py`: user config handling (`~/.pdf2audio/config.yml`, `.env`)
  - `data/`: `default_config.yml`, env template
- `assets/`: sample PDFs for local testing
- `requirements.txt`, `setup.py`, `build.py`: packaging and deps
- `tests/` (add as needed): pytest tests

## Build, Test, and Development Commands
- Setup (editable install):
  - `python -m venv venv && source venv/bin/activate`
  - `pip install -e .`
- Quick checks:
  - Dry run (extract + chunk only): `python -m pdf2audio.cli --pdf assets/test.pdf --mp3 out/test.mp3 --dry-run`
  - Full (gTTS, no LLM): `python -m pdf2audio.cli --pdf assets/test.pdf --mp3 out/test.mp3 --no-llm --ttsprovider gtts`
  - Cleaning example (needs `OPENAI_API_KEY`): `--cleaner-llm openai --lang es-MX`
  - Build package: `python setup.py sdist bdist_wheel` (or `python build.py`)

## Jobs & Manifests
- Every run writes a job manifest next to the MP3: `<mp3_dir>/<stem>.yml` summarizing inputs, params, and artifact paths.
- Resume without re-cleaning: `python -m pdf2audio.cli --job out/test.yml --mp3 out/test_new.mp3 --no-llm`
- Edit cleaned/summary text (under `<mp3_dir>/<stem>/`) and regenerate audio using `--job` to save LLM credits.
- JSON Schema for manifests: `pdf2audio/data/job.schema.json` (use with your preferred validator).
 - Validate a job file:
   - Module: `python scripts/validate_job.py out/test.yml`
   - CLI: `pdf2audio-validate-job out/test.yml`

## Coding Style & Naming Conventions
- Python, 4‑space indent, PEP 8 naming: `snake_case` functions/files, `PascalCase` classes.
- Keep modules cohesive; prefer small, testable functions.
- Don’t add heavy dependencies without discussion.
- Saved artifacts live beside the MP3 to reduce clutter:
  - Raw: `<mp3_dir>/<stem>/<stem>_raw.txt`
  - Cleaned: `<mp3_dir>/<stem>/<stem>_cleaned.txt`
  - SSML: `<mp3_dir>/<stem>/<stem>_ssml.txt`
  - Chunks: `<mp3_dir>/<stem>/<stem>_chunks/chunk_<n>.txt`

## Testing Guidelines
- Use `pytest`; place tests under `tests/` named `test_*.py`.
- Priorities: `preclean_text`, chunkers, provider max‑chunk logic, CLI argument mapping.
- Mock network calls (LLM/TTS) and file I/O; keep tests fast and offline.
- Run: `pytest -q`

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject, scoped if useful (e.g., `cli: ...`, `processors: ...`).
- PRs: describe intent, rationale, and user impact; include sample commands/output and updated docs when behavior changes.
- Ensure no secrets or credentials are committed; run a dry run before requesting review.

## Security & Configuration Tips
- Do not commit `.env` or keys. User config lives in `~/.pdf2audio/`.
- SSML support: only AWS/Google providers; gTTS/OpenAI TTS ignore SSML (guarded in CLI).
- Network is required for LLM cleaning and all cloud TTS.
