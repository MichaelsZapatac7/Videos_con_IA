"""
Voiceover generation using ElevenLabs API.
Converts script text to high-quality speech per segment.

(Proveedor "elevenlabs" — se mantiene intacto como respaldo. El selector
está en voiceover.py, que elige este módulo o voiceover_local.py según
la variable de entorno TTS_PROVIDER.)
"""

import os
import time
from pathlib import Path
from typing import Optional
import requests

from ..config import cfg


ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
ELEVENLABS_VOICES_URL = "https://api.elevenlabs.io/v1/voices"


def list_voices() -> list[dict]:
    """List available ElevenLabs voices."""
    resp = requests.get(
        ELEVENLABS_VOICES_URL,
        headers={"xi-api-key": cfg.elevenlabs_api_key},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["voices"]


def text_to_speech(
    text: str,
    output_path: Path,
    voice_id: Optional[str] = None,
    model: Optional[str] = None,
    stability: Optional[float] = None,
    similarity: Optional[float] = None,
) -> Path:
    """
    Generate speech audio from text using ElevenLabs.
    Returns the path to the generated audio file.
    """
    voice_id = voice_id or cfg.elevenlabs_voice_id
    model = model or cfg.elevenlabs_model
    stability = stability if stability is not None else cfg.elevenlabs_stability
    similarity = similarity if similarity is not None else cfg.elevenlabs_similarity

    url = ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    payload = {
        "text": text,
        "model_id": model,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity,
            "style": 0.3,
            "use_speaker_boost": True,
        },
    }

    resp = requests.post(
        url,
        json=payload,
        headers={
            "xi-api-key": cfg.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        timeout=60,
    )
    resp.raise_for_status()

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)
    return output_path


def generate_segment_voiceovers(
    segments: list[dict],
    output_dir: Path,
    voice_id: Optional[str] = None,
    delay_between_requests: float = 0.5,
) -> list[Path]:
    """
    Generate a voiceover audio file for each script segment.
    Returns list of audio file paths in segment order.
    """
    audio_paths = []
    for i, segment in enumerate(segments):
        text = segment.get("text", "")
        if not text.strip():
            continue

        out_path = output_dir / f"segment_{i:03d}.mp3"
        print(f"  [voiceover] Segment {i+1}/{len(segments)}: {text[:60]}...")
        text_to_speech(text, out_path, voice_id=voice_id)
        audio_paths.append(out_path)

        if i < len(segments) - 1:
            time.sleep(delay_between_requests)

    return audio_paths


def generate_full_voiceover(
    segments: list[dict],
    output_path: Path,
    voice_id: Optional[str] = None,
) -> Path:
    """
    Generate the complete voiceover as a single audio file.
    Concatenates all segment texts and generates one request.
    """
    full_text = " ".join(s.get("text", "") for s in segments)
    return text_to_speech(full_text, output_path, voice_id=voice_id)
