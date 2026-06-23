"""
Generación de voz LOCAL con clonación de voz (XTTS-v2 / Coqui TTS).

Reemplaza a ElevenLabs: usa TU propia voz a partir de una muestra de audio,
sin pagar API. Pensado para correr en GPU NVIDIA (ideal RTX serie 40/50).

Requiere el entorno virtual `.venv-voz` con `coqui-tts` + PyTorch CUDA.
Instrucciones completas: ver SETUP_VOZ_LOCAL.md en la raíz del proyecto.

La misma interfaz que voiceover_elevenlabs.py para que el resto del pipeline
(main.py, assembler) no necesite ningún cambio.
"""

import os
from pathlib import Path
from typing import Optional

from ..config import cfg

# Aceptar la licencia de Coqui sin prompt interactivo (Coqui Public Model License).
os.environ.setdefault("COQUI_TOS_AGREED", "1")

# El modelo es pesado: se carga UNA sola vez y se reutiliza (singleton).
_tts_model = None


def _get_model():
    """Carga (una vez) el modelo XTTS y lo deja en GPU."""
    global _tts_model
    if _tts_model is not None:
        return _tts_model

    import torch
    from TTS.api import TTS

    # PyTorch >= 2.6 usa weights_only=True por defecto al deserializar; XTTS
    # necesita que registremos sus clases como "safe globals" para cargar bien.
    try:
        from TTS.tts.configs.xtts_config import XttsConfig
        from TTS.tts.models.xtts import XttsAudioConfig, XttsArgs
        from TTS.config.shared_configs import BaseDatasetConfig
        torch.serialization.add_safe_globals(
            [XttsConfig, XttsAudioConfig, BaseDatasetConfig, XttsArgs]
        )
    except Exception:
        pass

    device = cfg.local_tts_device
    if device == "cuda" and not torch.cuda.is_available():
        print("  [voz-local] AVISO: CUDA no disponible → usando CPU (será lento).")
        device = "cpu"
    if device == "cuda":
        print(f"  [voz-local] GPU detectada: {torch.cuda.get_device_name(0)}")

    print(f"  [voz-local] Cargando modelo: {cfg.local_tts_model}")
    print("  [voz-local] (la primera vez descarga ~2 GB; luego queda en caché)")
    _tts_model = TTS(cfg.local_tts_model).to(device)
    print("  [voz-local] Modelo listo.")
    return _tts_model


def text_to_speech(
    text: str,
    output_path: Path,
    voice_id: Optional[str] = None,   # aquí: ruta a una muestra de voz alternativa
    **_ignored,                        # acepta args de ElevenLabs sin romper
) -> Path:
    """
    Genera audio con tu voz clonada y lo guarda como .wav.
    `voice_id` puede ser la ruta a otra muestra de voz; si no, usa la del config.
    """
    speaker_wav = voice_id or cfg.local_voice_sample
    if not Path(speaker_wav).exists():
        raise FileNotFoundError(
            f"No se encuentra tu muestra de voz: {speaker_wav}\n"
            "Graba tu voz y colócala ahí (ver SETUP_VOZ_LOCAL.md)."
        )

    model = _get_model()
    output_path = Path(output_path).with_suffix(".wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model.tts_to_file(
        text=text,
        speaker_wav=str(speaker_wav),
        language=cfg.local_tts_language,
        file_path=str(output_path),
        split_sentences=True,   # XTTS rinde mejor partiendo el texto en frases
    )
    return output_path


def generate_segment_voiceovers(
    segments: list[dict],
    output_dir: Path,
    voice_id: Optional[str] = None,
    delay_between_requests: float = 0.0,   # sin red: no hace falta esperar
) -> list[Path]:
    """Genera un .wav por cada segmento del guion. Carga el modelo una sola vez."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _get_model()  # precarga antes del bucle (evita medir mal el primer segmento)

    audio_paths: list[Path] = []
    for i, segment in enumerate(segments):
        text = segment.get("text", "")
        if not text.strip():
            continue
        out_path = output_dir / f"segment_{i:03d}.wav"
        print(f"  [voz-local] Segmento {i+1}/{len(segments)}: {text[:60]}...")
        text_to_speech(text, out_path, voice_id=voice_id)
        audio_paths.append(out_path)
    return audio_paths


def generate_full_voiceover(
    segments: list[dict],
    output_path: Path,
    voice_id: Optional[str] = None,
) -> Path:
    """Genera todo el guion como un único archivo de audio."""
    full_text = " ".join(s.get("text", "") for s in segments)
    return text_to_speech(full_text, output_path, voice_id=voice_id)
