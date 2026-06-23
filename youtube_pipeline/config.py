"""
Centralized configuration — all API keys come from environment variables.
Copy .env.example to .env and fill in your keys before running.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
ASSETS_DIR = BASE_DIR / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
FONTS_DIR = ASSETS_DIR / "fonts"

for d in [OUTPUT_DIR, ASSETS_DIR, MUSIC_DIR, FONTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader (no external dependency). Existing env vars win."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        # Strip surrounding quotes and inline comments-free value
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv(BASE_DIR / ".env")


@dataclass
class Config:
    # API Keys
    anthropic_api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    elevenlabs_api_key: str = field(default_factory=lambda: os.environ.get("ELEVENLABS_API_KEY", ""))
    pexels_api_key: str = field(default_factory=lambda: os.environ.get("PEXELS_API_KEY", ""))
    higgsfield_api_key: str = field(default_factory=lambda: os.environ.get("HIGGSFIELD_API_KEY", ""))

    # ElevenLabs voice settings
    elevenlabs_voice_id: str = field(default_factory=lambda: os.environ.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM"))  # Rachel
    elevenlabs_model: str = "eleven_multilingual_v2"
    elevenlabs_stability: float = 0.5
    elevenlabs_similarity: float = 0.75

    # ── Proveedor de voz ─────────────────────────────────────────────────────
    # "elevenlabs" (API de pago, por defecto) o "local" (tu voz clonada, gratis)
    tts_provider: str = field(default_factory=lambda: os.environ.get("TTS_PROVIDER", "elevenlabs"))

    # Voz local (XTTS-v2 / Coqui TTS) — solo se usa si tts_provider == "local"
    local_voice_sample: str = field(default_factory=lambda: os.environ.get(
        "LOCAL_VOICE_SAMPLE", str(ASSETS_DIR / "voces" / "mi_voz.wav")))
    local_tts_model: str = field(default_factory=lambda: os.environ.get(
        "LOCAL_TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2"))
    local_tts_language: str = field(default_factory=lambda: os.environ.get("LOCAL_TTS_LANGUAGE", "es"))
    local_tts_device: str = field(default_factory=lambda: os.environ.get("LOCAL_TTS_DEVICE", "cuda"))

    # Claude model for script generation
    claude_model: str = "claude-sonnet-4-6"

    # Video settings
    video_width: int = 1920
    video_height: int = 1080
    video_fps: int = 30
    shorts_width: int = 1080
    shorts_height: int = 1920

    # Output quality
    video_bitrate: str = "5000k"
    audio_bitrate: str = "192k"

    # Channel branding
    channel_name: str = os.environ.get("CHANNEL_NAME", "@mzcshard")
    primary_color: str = os.environ.get("PRIMARY_COLOR", "#FF6B35")
    secondary_color: str = os.environ.get("SECONDARY_COLOR", "#1A1A2E")
    font_family: str = "Arial"

    # Paths
    output_dir: Path = OUTPUT_DIR
    assets_dir: Path = ASSETS_DIR
    music_dir: Path = MUSIC_DIR
    fonts_dir: Path = FONTS_DIR


cfg = Config()
