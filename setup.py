#!/usr/bin/env python3

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
if (this_directory / "requirements.txt").exists():
    requirements = (this_directory / "requirements.txt").read_text().strip().split('\n')
    requirements = [req.strip() for req in requirements if req.strip() and not req.startswith('#')]

setup(
    name="pdf2audio",
    version="2.1.0",
    author="zenbakiak",
    author_email="zenbakiak@users.noreply.github.com",
    description="Convert PDF documents to audio using various TTS providers and AI-powered text cleaning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/zenbakiak/pdf2audio",
    packages=find_packages(include=['pdf2audio', 'pdf2audio.*']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Office/Business :: Office Suites",
        "Topic :: Text Processing :: Markup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pdf2audio=pdf2audio.cli:main",
            "pdf-to-audio=pdf2audio.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "pdf2audio": [
            "data/default_config.yml",
            "data/.env.example",
        ],
    },
    keywords="pdf, audio, tts, text-to-speech, openai, aws, polly, gtts, accessibility",
    project_urls={
        "Bug Reports": "https://github.com/zenbakiak/pdf2audio/issues",
        "Source": "https://github.com/zenbakiak/pdf2audio",
        "Documentation": "https://github.com/zenbakiak/pdf2audio#readme",
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.900",
        ],
        "all": [
            "openai>=1.0.0",
            "google-generativeai>=0.3.0", 
            "azure-cognitiveservices-speech>=1.30.0",
            "boto3>=1.26.0",
        ],
    },
)
