"""
ElevenLabs Audio Service
Provides text-to-speech, speech-to-text, and audio generation capabilities.
"""

import asyncio
import logging
import os
from io import BytesIO
from typing import AsyncIterator, BinaryIO

try:
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    ElevenLabs = None

from fastapi import HTTPException

from app.config import get_settings

logger = logging.getLogger("nebula.audio")
settings = get_settings()


class AudioService:
    """Service for ElevenLabs audio operations."""
    
    def __init__(self):
        """Initialize ElevenLabs client."""
        if not ELEVENLABS_AVAILABLE:
            logger.warning("elevenlabs package not installed - audio features disabled")
            self.client = None
            return
            
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ELEVENLABS_API_KEY not set - audio features disabled")
            self.client = None
        else:
            self.client = ElevenLabs(api_key=api_key)
        
        # Default voice settings optimized for clarity
        self.default_voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
    
    def is_available(self) -> bool:
        """Check if audio service is available."""
        return self.client is not None
    
    async def text_to_speech(
        self,
        text: str,
        voice: str = "Rachel",
        model: str = "eleven_monolingual_v1",
        optimize_streaming: bool = False
    ) -> bytes:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            voice: Voice name (e.g., "Rachel", "Adam", "Bella")
            model: TTS model to use
            optimize_streaming: Enable streaming latency optimization
            
        Returns:
            Audio data as bytes (MP3 format)
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Audio service unavailable - API key not configured"
            )
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            audio_generator = await loop.run_in_executor(
                None,
                lambda: self.client.generate(
                    text=text,
                    voice=voice,
                    model=model,
                    voice_settings=self.default_voice_settings,
                    optimize_streaming_latency=optimize_streaming
                )
            )
            
            # Collect audio chunks
            audio_data = BytesIO()
            for chunk in audio_generator:
                audio_data.write(chunk)
            
            return audio_data.getvalue()
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio generation failed: {str(e)}"
            )
    
    async def text_to_speech_stream(
        self,
        text: str,
        voice: str = "Rachel",
        model: str = "eleven_monolingual_v1"
    ) -> AsyncIterator[bytes]:
        """
        Convert text to speech with streaming response.
        Useful for real-time playback of long content.
        
        Args:
            text: Text to convert
            voice: Voice name
            model: TTS model
            
        Yields:
            Audio chunks as bytes
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Audio service unavailable"
            )
        
        try:
            loop = asyncio.get_event_loop()
            audio_generator = await loop.run_in_executor(
                None,
                lambda: self.client.generate(
                    text=text,
                    voice=voice,
                    model=model,
                    voice_settings=self.default_voice_settings,
                    optimize_streaming_latency=True,
                    stream=True
                )
            )
            
            for chunk in audio_generator:
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming TTS error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Audio streaming failed: {str(e)}"
            )
    
    async def speech_to_text(
        self,
        audio_file: BinaryIO,
        language: str = "en"
    ) -> dict:
        """
        Transcribe audio file to text.
        
        Args:
            audio_file: Audio file (MP3, WAV, etc.)
            language: Language code (e.g., "en", "es", "fr")
            
        Returns:
            Dict with transcription text and metadata
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Audio service unavailable"
            )
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.client.speech_to_text.transcribe(
                    audio=audio_file,
                    language_code=language
                )
            )
            
            return {
                "text": result.text,
                "language": language,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Speech-to-text error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Transcription failed: {str(e)}"
            )
    
    async def generate_sound_effect(
        self,
        description: str,
        duration_seconds: float = 2.0,
        prompt_influence: float = 0.3
    ) -> bytes:
        """
        Generate a sound effect from text description.
        
        Args:
            description: Description of the sound (e.g., "notification bell")
            duration_seconds: Length of sound effect
            prompt_influence: How closely to follow the prompt (0-1)
            
        Returns:
            Audio data as bytes
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Audio service unavailable"
            )
        
        try:
            loop = asyncio.get_event_loop()
            audio_generator = await loop.run_in_executor(
                None,
                lambda: self.client.sound_generation.generate(
                    text=description,
                    duration_seconds=duration_seconds,
                    prompt_influence=prompt_influence
                )
            )
            
            audio_data = BytesIO()
            for chunk in audio_generator:
                audio_data.write(chunk)
            
            return audio_data.getvalue()
            
        except Exception as e:
            logger.error(f"Sound effect generation error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Sound generation failed: {str(e)}"
            )
    
    async def list_voices(self) -> list[dict]:
        """
        Get list of available voices.
        
        Returns:
            List of voice dictionaries with name, ID, and metadata
        """
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Audio service unavailable"
            )
        
        try:
            loop = asyncio.get_event_loop()
            voices_response = await loop.run_in_executor(
                None,
                self.client.voices.get_all
            )
            
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "description": voice.description,
                    "preview_url": voice.preview_url
                }
                for voice in voices_response.voices
            ]
            
        except Exception as e:
            logger.error(f"List voices error: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list voices: {str(e)}"
            )
    
    def format_search_results_for_narration(
        self,
        query: str,
        results: list[dict],
        max_results: int = 5
    ) -> str:
        """
        Format search results into natural narration text.
        
        Args:
            query: Original search query
            results: List of search result dicts
            max_results: Maximum number of results to narrate
            
        Returns:
            Formatted text for narration
        """
        if not results:
            return f"No results found for: {query}"
        
        narration_parts = [
            f"Here are the top {min(len(results), max_results)} results for: {query}."
        ]
        
        for i, result in enumerate(results[:max_results], 1):
            title = result.get("title", "Untitled")
            snippet = result.get("snippet", "")
            source = result.get("source", "")
            
            # Clean snippet (remove extra whitespace)
            snippet = " ".join(snippet.split())
            
            part = f"Result {i}: {title}. "
            if snippet:
                part += f"{snippet} "
            if source:
                part += f"Source: {source}."
            
            narration_parts.append(part)
        
        return " ".join(narration_parts)
    
    def format_notification(
        self,
        message: str,
        notification_type: str = "info"
    ) -> str:
        """
        Format notification message for audio narration.
        
        Args:
            message: Notification message
            notification_type: Type (info, success, warning, error)
            
        Returns:
            Formatted text for narration
        """
        prefixes = {
            "info": "Information: ",
            "success": "Success: ",
            "warning": "Warning: ",
            "error": "Error: "
        }
        
        prefix = prefixes.get(notification_type, "")
        return f"{prefix}{message}"


# Global audio service instance
audio_service = AudioService()
