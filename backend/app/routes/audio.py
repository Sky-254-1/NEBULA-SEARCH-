"""Audio API routes for ElevenLabs integration."""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import Response, StreamingResponse

from app.middleware.rate_limit import rate_limit
from app.services.audio import audio_service
from app.services.auth import get_current_user

logger = logging.getLogger("nebula.audio")

router = APIRouter(prefix="/api/v1/audio", tags=["Audio"])


@router.get("/health")
async def audio_health():
    """Check if audio service is available."""
    return {
        "available": audio_service.is_available(),
        "service": "ElevenLabs",
        "features": [
            "text-to-speech",
            "speech-to-text",
            "sound-effects",
            "search-narration",
            "notifications"
        ]
    }


@router.get("/voices")
async def list_voices(
    email: str = Depends(get_current_user)
):
    """List available voices for text-to-speech."""
    voices = await audio_service.list_voices()
    return {"voices": voices, "total": len(voices)}


@router.post(
    "/tts",
    response_class=Response,
    dependencies=[Depends(rate_limit)]
)
async def text_to_speech(
    text: Annotated[str, Body(embed=True, min_length=1, max_length=5000)],
    voice: Annotated[str, Body(embed=True)] = "Rachel",
    optimize_streaming: Annotated[bool, Body(embed=True)] = False,
    email: str = Depends(get_current_user)
):
    """
    Convert text to speech audio.
    
    Returns MP3 audio data.
    """
    audio_data = await audio_service.text_to_speech(
        text=text,
        voice=voice,
        optimize_streaming=optimize_streaming
    )
    
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "Cache-Control": "public, max-age=3600"
        }
    )


@router.post(
    "/tts/stream",
    response_class=StreamingResponse,
    dependencies=[Depends(rate_limit)]
)
async def text_to_speech_stream(
    text: Annotated[str, Body(embed=True, min_length=1, max_length=10000)],
    voice: Annotated[str, Body(embed=True)] = "Rachel",
    email: str = Depends(get_current_user)
):
    """
    Stream text-to-speech audio for real-time playback.
    
    Useful for long content like articles or search result narration.
    """
    return StreamingResponse(
        audio_service.text_to_speech_stream(text=text, voice=voice),
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech_stream.mp3",
            "Cache-Control": "no-cache"
        }
    )


@router.post("/stt", dependencies=[Depends(rate_limit)])
async def speech_to_text(
    audio: UploadFile = File(..., description="Audio file (MP3, WAV, etc.)"),
    language: str = Form("en", description="Language code"),
    email: str = Depends(get_current_user)
):
    """
    Transcribe audio to text (speech-to-text).
    
    Supports voice search and audio transcription.
    """
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type - must be audio"
        )
    
    # Read audio file
    audio_content = await audio.read()
    
    # Create file-like object
    from io import BytesIO
    audio_file = BytesIO(audio_content)
    audio_file.name = audio.filename or "audio.mp3"
    
    result = await audio_service.speech_to_text(
        audio_file=audio_file,
        language=language
    )
    
    return result


@router.post(
    "/narrate/search",
    response_class=Response,
    dependencies=[Depends(rate_limit)]
)
async def narrate_search_results(
    query: Annotated[str, Body(embed=True)],
    results: Annotated[list[dict], Body(embed=True)],
    max_results: Annotated[int, Body(embed=True)] = 5,
    voice: Annotated[str, Body(embed=True)] = "Rachel",
    email: str = Depends(get_current_user)
):
    """
    Generate audio narration of search results.
    
    Useful for accessibility and hands-free search.
    """
    # Format results into narration text
    narration_text = audio_service.format_search_results_for_narration(
        query=query,
        results=results,
        max_results=max_results
    )
    
    # Generate audio
    audio_data = await audio_service.text_to_speech(
        text=narration_text,
        voice=voice,
        optimize_streaming=True
    )
    
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="search_narration.mp3"',
            "Cache-Control": "public, max-age=1800"
        }
    )


@router.post(
    "/notification",
    response_class=Response,
    dependencies=[Depends(rate_limit)]
)
async def audio_notification(
    message: Annotated[str, Body(embed=True, min_length=1, max_length=500)],
    notification_type: Annotated[str, Body(embed=True)] = "info",
    voice: Annotated[str, Body(embed=True)] = "Rachel",
    email: str = Depends(get_current_user)
):
    """
    Generate audio notification.
    
    Types: info, success, warning, error
    """
    valid_types = ["info", "success", "warning", "error"]
    if notification_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid notification type. Must be one of: {valid_types}"
        )
    
    # Format notification
    notification_text = audio_service.format_notification(
        message=message,
        notification_type=notification_type
    )
    
    # Generate audio
    audio_data = await audio_service.text_to_speech(
        text=notification_text,
        voice=voice,
        optimize_streaming=True
    )
    
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=notification.mp3",
            "Cache-Control": "no-cache"
        }
    )


@router.post(
    "/sound-effect",
    response_class=Response,
    dependencies=[Depends(rate_limit)]
)
async def generate_sound_effect(
    description: Annotated[str, Body(embed=True, min_length=1, max_length=200)],
    duration: Annotated[float, Body(embed=True, ge=0.5, le=10.0)] = 2.0,
    email: str = Depends(get_current_user)
):
    """
    Generate custom sound effect from description.
    
    Examples:
    - "notification bell"
    - "success chime"
    - "error buzzer"
    - "page turn"
    """
    audio_data = await audio_service.generate_sound_effect(
        description=description,
        duration_seconds=duration
    )
    
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": 'inline; filename="sound_effect.mp3"',
            "Cache-Control": "public, max-age=86400"  # Cache for 24h
        }
    )


@router.post(
    "/podcast/generate",
    response_class=Response,
    dependencies=[Depends(rate_limit)]
)
async def generate_podcast(
    title: Annotated[str, Body(embed=True)],
    content: Annotated[str, Body(embed=True, min_length=100, max_length=50000)],
    voice: Annotated[str, Body(embed=True)] = "Rachel",
    add_intro: Annotated[bool, Body(embed=True)] = True,
    email: str = Depends(get_current_user)
):
    """
    Generate podcast-style audio from long-form content.
    
    Useful for converting articles, documents, or search results
    into podcast episodes.
    """
    # Add intro if requested
    if add_intro:
        intro = f"Welcome to Nebula Search Podcast. Today's topic: {title}. "
        full_content = intro + content
    else:
        full_content = content
    
    # Generate audio with streaming optimization
    audio_data = await audio_service.text_to_speech(
        text=full_content,
        voice=voice,
        optimize_streaming=True
    )
    
    # Clean filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
    safe_title = safe_title.replace(' ', '_')[:50]
    
    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f'attachment; filename="podcast_{safe_title}.mp3"',
            "Cache-Control": "public, max-age=3600"
        }
    )
