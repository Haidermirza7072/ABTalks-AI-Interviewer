import asyncio
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["TTS"])


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    voice: str = Field(default="en-US-GuyNeural", min_length=1, max_length=100)
    rate: str = Field(default="+0%", max_length=20)


NATURAL_VOICES = {
    "en-US-GuyNeural",
    "en-US-AriaNeural",
    "en-US-JennyNeural",
    "en-US-ChristopherNeural",
    "en-US-EricNeural",
    "en-US-MichelleNeural",
    "en-GB-RyanNeural",
    "en-GB-SoniaNeural",
    "en-GB-LibbyNeural",
}


@router.post(
    "/",
    summary="Convert text to natural speech audio",
    responses={
        200: {"content": {"audio/mpeg": {}}, "description": "Synthesized MP3 audio"},
        422: {"description": "Validation error"},
        502: {"description": "TTS synthesis failed"},
    },
)
async def synthesize_speech(payload: TTSRequest):
    """Synthesize natural human-like speech using Microsoft Edge neural voices."""
    import edge_tts  # imported lazily so the app boots even if not installed

    voice = payload.voice if payload.voice in NATURAL_VOICES else "en-US-GuyNeural"

    try:
        communicate = edge_tts.Communicate(
            text=payload.text,
            voice=voice,
            rate=payload.rate,
            pitch="+0Hz",
        )
        audio = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.extend(chunk["data"])
        if not audio:
            raise RuntimeError("Empty audio stream returned by TTS engine")
        return Response(
            content=bytes(audio),
            media_type="audio/mpeg",
            headers={"Cache-Control": "no-store"},
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.error(f"TTS synthesis failed: {exc}")
        raise HTTPException(
            status_code=502,
            detail="TTS synthesis failed. Ensure network access is available.",
        ) from exc
