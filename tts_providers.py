#!/usr/bin/env python3

from abc import ABC, abstractmethod
import os
from typing import List, Optional
from gtts import gTTS
from openai import OpenAI
import boto3
from pydub import AudioSegment
from config import Config


def chunk_text(text: str, max_length: int = 4000) -> List[str]:
    """Split text into chunks that respect sentence boundaries."""
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by sentences (periods, exclamation marks, question marks)
    sentences = text.replace('!', '.').replace('?', '.').split('.')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
            
        # Add the period back
        sentence += '.'
        
        # If adding this sentence would exceed the limit, save current chunk
        if len(current_chunk) + len(sentence) > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                # Single sentence is too long, split by words
                words = sentence.split()
                temp_chunk = ""
                for word in words:
                    if len(temp_chunk) + len(word) + 1 > max_length:
                        if temp_chunk:
                            chunks.append(temp_chunk.strip())
                            temp_chunk = word
                        else:
                            # Single word is too long, force split
                            chunks.append(word[:max_length])
                            temp_chunk = word[max_length:]
                    else:
                        temp_chunk += " " + word if temp_chunk else word
                if temp_chunk:
                    current_chunk = temp_chunk
        else:
            current_chunk += " " + sentence if current_chunk else sentence
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def validate_speaking_rate(speaking_rate: float) -> float:
    """Validate speaking rate is within acceptable range."""
    if speaking_rate < 0.25 or speaking_rate > 2.0:
        raise ValueError(f"speaking_rate must be in range [0.25, 2.0], got {speaking_rate}")
    return speaking_rate


def adjust_audio_speed(input_path: str, output_path: str, speaking_rate: float) -> None:
    """Adjust audio speed using pydub."""
    try:
        audio = AudioSegment.from_mp3(input_path)
        
        if speaking_rate == 1.0:
            return
        
        playback_speed = speaking_rate
        adjusted_audio = audio.speedup(playback_speed=playback_speed)
        adjusted_audio.export(output_path, format="mp3")
        
        if os.path.exists(input_path) and input_path != output_path:
            os.remove(input_path)
        
        print(f"Audio speed adjusted to {speaking_rate}x")
    except Exception as e:
        print(f"Warning: Could not adjust audio speed: {e}")
        if input_path != output_path:
            import shutil
            shutil.move(input_path, output_path)


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""
    
    def __init__(self, config: Config):
        self.config = config
    
    @abstractmethod
    def synthesize(self, text: str, output_path: str, language: str = 'en') -> None:
        """Synthesize text to speech."""
        pass


class GoogleTTS(TTSProvider):
    """Google Text-to-Speech provider."""
    
    def synthesize(self, text: str, output_path: str, language: str = 'en') -> None:
        """Synthesize text using Google TTS."""
        speaking_rate = self.config.speaking_rate
        
        if speaking_rate != 1.0:
            validate_speaking_rate(speaking_rate)
        
        temp_output = output_path
        if speaking_rate != 1.0:
            temp_output = output_path.replace('.mp3', '_temp.mp3')
        
        slow = self.config.get('tts.slow', False)
        tts = gTTS(text=text, lang=language, slow=slow)
        tts.save(temp_output)
        
        if speaking_rate != 1.0:
            if self.config.verbose:
                print(f"Adjusting audio speed to {speaking_rate}x...")
            adjust_audio_speed(temp_output, output_path, speaking_rate)


class OpenAITTS(TTSProvider):
    """OpenAI Text-to-Speech provider."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """Create OpenAI client."""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        try:
            return OpenAI(api_key=api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client. Error: {e}")
    
    def synthesize(self, text: str, output_path: str, language: str = 'en') -> None:
        """Synthesize text using OpenAI TTS."""
        voice_config = self.config.get_tts_config('openai')
        speaking_rate = self.config.speaking_rate
        
        # Check if text needs to be chunked
        max_chars = 4000  # Leave some buffer below 4096
        if len(text) <= max_chars:
            # Single request
            response = self.client.audio.speech.create(
                model=voice_config.get('model', 'tts-1'),
                voice=voice_config.get('voice', 'alloy'),
                input=text,
                speed=speaking_rate
            )
            response.stream_to_file(output_path)
        else:
            # Split text into chunks and combine audio
            if self.config.verbose:
                print(f"Text is {len(text)} characters, splitting into chunks...")
            
            chunks = chunk_text(text, max_chars)
            if self.config.verbose:
                print(f"Split into {len(chunks)} chunks")
            
            audio_segments = []
            temp_files = []
            
            try:
                for i, chunk in enumerate(chunks):
                    temp_file = output_path.replace('.mp3', f'_chunk_{i}.mp3')
                    temp_files.append(temp_file)
                    
                    if self.config.verbose:
                        print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
                    
                    response = self.client.audio.speech.create(
                        model=voice_config.get('model', 'tts-1'),
                        voice=voice_config.get('voice', 'alloy'),
                        input=chunk,
                        speed=speaking_rate
                    )
                    response.stream_to_file(temp_file)
                    
                    # Load audio segment
                    audio_segments.append(AudioSegment.from_mp3(temp_file))
                
                # Combine all audio segments
                if self.config.verbose:
                    print("Combining audio chunks...")
                
                combined_audio = audio_segments[0]
                for segment in audio_segments[1:]:
                    combined_audio = combined_audio + segment
                
                # Export combined audio
                combined_audio.export(output_path, format="mp3")
                
            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)


class AWSTTS(TTSProvider):
    """AWS Polly TTS provider."""
    
    def __init__(self, config: Config):
        super().__init__(config)
        self.client = self._create_client()
    
    def _create_client(self):
        """Create AWS Polly client."""
        aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
        aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
        
        if not aws_key or not aws_secret:
            raise ValueError("AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables must be set for AWS Polly TTS")
        
        return boto3.client('polly',
            aws_access_key_id=aws_key,
            aws_secret_access_key=aws_secret,
            region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        )
    
    def synthesize(self, text: str, output_path: str, language: str = 'en') -> None:
        """Synthesize text using AWS Polly."""
        voice_config = self.config.get_tts_config('aws')
        speaking_rate = self.config.speaking_rate
        
        rate_percent = int((speaking_rate - 1.0) * 100)
        rate_value = f"{rate_percent:+d}%" if rate_percent != 0 else "0%"
        
        # AWS Polly limit is ~3000 billable chars, use 2800 as safe limit
        max_chars = 2800
        
        if len(text) <= max_chars:
            # Single request
            ssml = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
                <prosody rate="{rate_value}">
                    {text}
                </prosody>
            </speak>
            """
            
            response = self.client.synthesize_speech(
                Text=ssml,
                TextType='ssml',
                OutputFormat='mp3',
                VoiceId=voice_config.get('voice_id', 'Joanna'),
                Engine=voice_config.get('engine', 'neural'),
                LanguageCode=language
            )
            
            with open(output_path, 'wb') as f:
                f.write(response['AudioStream'].read())
        else:
            # Split text into chunks and combine audio
            if self.config.verbose:
                print(f"Text is {len(text)} characters, splitting into chunks for AWS Polly...")
            
            chunks = chunk_text(text, max_chars)
            if self.config.verbose:
                print(f"Split into {len(chunks)} chunks")
            
            audio_segments = []
            temp_files = []
            
            try:
                for i, chunk in enumerate(chunks):
                    temp_file = output_path.replace('.mp3', f'_chunk_{i}.mp3')
                    temp_files.append(temp_file)
                    
                    if self.config.verbose:
                        print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
                    
                    ssml = f"""
                    <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{language}">
                        <prosody rate="{rate_value}">
                            {chunk}
                        </prosody>
                    </speak>
                    """
                    
                    response = self.client.synthesize_speech(
                        Text=ssml,
                        TextType='ssml',
                        OutputFormat='mp3',
                        VoiceId=voice_config.get('voice_id', 'Joanna'),
                        Engine=voice_config.get('engine', 'neural'),
                        LanguageCode=language
                    )
                    
                    with open(temp_file, 'wb') as f:
                        f.write(response['AudioStream'].read())
                    
                    # Load audio segment
                    audio_segments.append(AudioSegment.from_mp3(temp_file))
                
                # Combine all audio segments
                if self.config.verbose:
                    print("Combining audio chunks...")
                
                combined_audio = audio_segments[0]
                for segment in audio_segments[1:]:
                    combined_audio = combined_audio + segment
                
                # Export combined audio
                combined_audio.export(output_path, format="mp3")
                
            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)


class TTSFactory:
    """Factory for creating TTS providers."""
    
    @staticmethod
    def create_provider(provider_name: str, config: Config) -> TTSProvider:
        """Create TTS provider based on name."""
        providers = {
            'gtts': GoogleTTS,
            'openai': OpenAITTS,
            'aws': AWSTTS
        }
        
        provider_class = providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Unsupported TTS provider: {provider_name}")
        
        return provider_class(config)