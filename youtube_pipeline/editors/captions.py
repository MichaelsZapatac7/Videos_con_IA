"""
Auto-caption generation using OpenAI Whisper (local, free).
Produces SRT subtitle files from audio/video.
"""

import subprocess
import json
from pathlib import Path
from typing import Optional


def transcribe_with_whisper(
    audio_path: Path,
    output_dir: Path,
    model: str = "base",
    language: Optional[str] = None,
) -> Path:
    """
    Transcribe audio using the `whisper` CLI tool and produce an SRT file.
    Returns the path to the .srt file.

    Args:
        audio_path: Path to audio or video file
        output_dir: Directory where SRT will be saved
        model: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
        language: Force language (e.g. 'es', 'en'). Auto-detects if None.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "whisper", str(audio_path),
        "--model", model,
        "--output_dir", str(output_dir),
        "--output_format", "srt",
    ]
    if language:
        cmd += ["--language", language]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"Whisper failed: {result.stderr[-500:]}")

    # Whisper saves the file as {audio_name}.srt
    srt_path = output_dir / (audio_path.stem + ".srt")
    if not srt_path.exists():
        raise FileNotFoundError(f"Expected SRT at {srt_path} but not found. Whisper output: {result.stdout[-200:]}")
    return srt_path


def transcribe_with_api(
    audio_path: Path,
    output_dir: Path,
    anthropic_api_key: str,
    language: Optional[str] = "es",
) -> Path:
    """
    Fallback: Use the OpenAI Whisper API for transcription.
    Requires the openai package: pip install openai
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("pip install openai  (needed for API-based transcription)")

    client = OpenAI()
    with open(audio_path, "rb") as f:
        params = {"model": "whisper-1", "response_format": "srt"}
        if language:
            params["language"] = language
        srt_content = client.audio.transcriptions.create(file=f, **params)

    output_dir.mkdir(parents=True, exist_ok=True)
    srt_path = output_dir / (audio_path.stem + ".srt")
    srt_path.write_text(srt_content, encoding="utf-8")
    return srt_path


def segments_to_srt(segments: list[dict], audio_paths: list[Path], output_path: Path) -> Path:
    """
    Build an SRT from script segments + per-segment audio duration.
    Used when Whisper is not available — creates approximate timing.
    """
    lines = []
    cursor = 0.0
    cue_index = 1

    for segment, audio_path in zip(segments, audio_paths):
        # Estimate duration from audio file via ffprobe
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio_path)],
                capture_output=True, text=True
            )
            duration = float(result.stdout.strip())
        except Exception:
            duration = segment.get("duration_seconds", 10)

        text = segment.get("text", "").strip()
        # Break the segment into short caption phrases (~max 7 words / 42 chars)
        phrases = _split_into_phrases(text, max_words=7, max_chars=42)
        if not phrases:
            cursor += duration
            continue

        # Distribute the segment duration across phrases proportionally to length
        total_chars = sum(len(p) for p in phrases) or 1
        sub_cursor = cursor
        for phrase in phrases:
            share = len(phrase) / total_chars
            phrase_dur = max(0.8, duration * share)
            start = _seconds_to_srt_time(sub_cursor)
            end = _seconds_to_srt_time(min(cursor + duration, sub_cursor + phrase_dur))
            lines.append(f"{cue_index}\n{start} --> {end}\n{phrase}\n")
            cue_index += 1
            sub_cursor += phrase_dur

        cursor += duration

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


def _split_into_phrases(text: str, max_words: int = 7, max_chars: int = 42) -> list[str]:
    """Split text into short caption-sized phrases, preferring sentence breaks."""
    words = text.split()
    phrases = []
    chunk = []
    for word in words:
        chunk.append(word)
        candidate = " ".join(chunk)
        # Flush on length limits or natural punctuation breaks
        ends_sentence = word.endswith((".", "!", "?", ":"))
        if len(chunk) >= max_words or len(candidate) >= max_chars or ends_sentence:
            phrases.append(candidate)
            chunk = []
    if chunk:
        phrases.append(" ".join(chunk))
    return phrases


def _seconds_to_srt_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
