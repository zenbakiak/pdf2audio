# Changelog

All notable changes to this project will be documented in this file.

## [2.1.0] - 2025-08-12
- Added `--summarize` flag (replaces `--summary`) to generate audiobook‑style summaries; requires `--cleaner-llm`.
- Added `--summary-lang` to control summary language; defaults to `--lang` or config language.
- Enforced minimum summary length via config:
  - `llm.min_summary_ratio` (default 0.45) and `llm.summary_ratio_tolerance` (default 0.9).
  - Summarization now targets ≥ 45% of original word count and expands if too short.
- Organized artifacts: when saving raw/cleaned/chunks, files are placed beside the MP3 in `<mp3_dir>/<stem>/` and `<stem>_chunks/`.
- SSML guard: auto‑disables `--use-ssml` for providers without SSML (gTTS/OpenAI TTS) with a warning.
- Language mapping: map `es-MX` → `es` for gTTS compatibility.
- Documentation: updated README and added contributor guide `AGENTS.md`.

## [2.0.0] - 2024-??-??
- Initial refactor with LLM cleaning, multiple TTS providers, and CLI.

[2.1.0]: https://github.com/zenbakiak/pdf2audio/compare/v2.0.0...v2.1.0
