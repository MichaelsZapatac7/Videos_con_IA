"""
Selector de proveedor de voz (voiceover).

Según la variable de entorno TTS_PROVIDER decide qué motor usar:
  - "elevenlabs" (por defecto) → voiceover_elevenlabs.py  (API de pago)
  - "local"                    → voiceover_local.py        (tu voz clonada, gratis)

El resto del pipeline (main.py, assembler) sigue importando desde aquí:
    from .voiceover import generate_segment_voiceovers, text_to_speech
…sin enterarse de cuál motor está activo.
"""

from ..config import cfg

# list_voices es específico de ElevenLabs y es liviano (solo requests),
# así que siempre lo exponemos desde ese módulo.
from .voiceover_elevenlabs import list_voices  # noqa: F401

_provider = (cfg.tts_provider or "elevenlabs").strip().lower()

if _provider == "f5":
    # Import perezoso: solo aquí se cargan torch / f5_tts (pesados).
    from .voiceover_f5 import (  # noqa: F401
        text_to_speech,
        generate_segment_voiceovers,
        generate_full_voiceover,
    )
elif _provider == "local":
    # Import perezoso: solo aquí se cargan torch / TTS (pesados).
    from .voiceover_local import (  # noqa: F401
        text_to_speech,
        generate_segment_voiceovers,
        generate_full_voiceover,
    )
else:
    from .voiceover_elevenlabs import (  # noqa: F401
        text_to_speech,
        generate_segment_voiceovers,
        generate_full_voiceover,
    )


def active_provider() -> str:
    """Nombre legible del proveedor de voz activo."""
    return {
        "f5": "tu voz local (F5-TTS español)",
        "local": "tu voz local (XTTS)",
    }.get(_provider, "ElevenLabs")
