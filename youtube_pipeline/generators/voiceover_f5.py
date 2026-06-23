"""
Generación de voz LOCAL con F5-TTS (modelo en español).

Clona TU voz con mejor fidelidad de acento (latino) y más naturalidad que XTTS.
Pensado para GPU NVIDIA (probado en RTX 5090 con PyTorch cu128).

A diferencia de XTTS, F5-TTS necesita la muestra de voz JUNTO con su
transcripción exacta (cfg.f5_ref_sample + cfg.f5_ref_text).

Misma interfaz que voiceover_elevenlabs.py / voiceover_local.py para que el
resto del pipeline (main.py, assembler) no cambie.
"""

import os
import glob
from pathlib import Path
from typing import Optional

from ..config import cfg

# Evitar el almacenamiento "Xet" de Hugging Face (host que algunos DNS no resuelven).
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")


def _register_ffmpeg_dlls() -> None:
    """
    torch >= 2.9 carga audio con torchcodec, que en Windows necesita las DLLs
    *compartidas* de FFmpeg 4–7. Incluimos un FFmpeg 7 "shared" dentro de
    .venv-voz y registramos su carpeta `bin` ANTES de importar torch/f5_tts.
    Sin esto, F5 falla al hacer torchaudio.load de la referencia.
    """
    if os.name != "nt":
        return
    override = os.environ.get("LOCAL_FFMPEG_DLL_DIR")
    candidates = [override] if override else []
    venv = Path(__file__).resolve().parents[2] / ".venv-voz" / "ffmpeg7-shared"
    candidates += glob.glob(str(venv / "*" / "bin"))
    for c in candidates:
        if c and Path(c, "avcodec-61.dll").exists():
            try:
                os.add_dll_directory(c)
            except (OSError, AttributeError):
                pass
            return


# El modelo es pesado: se carga UNA sola vez y se reutiliza (singleton).
_f5_model = None


def _get_model():
    """Carga (una vez) el modelo F5-TTS español y lo deja en GPU."""
    global _f5_model
    if _f5_model is not None:
        return _f5_model

    # Orden de DLLs: FFmpeg 7 -> torch -> f5_tts (imprescindible en Windows).
    _register_ffmpeg_dlls()
    import torch  # noqa: F401  (inicializa CUDA/DLLs antes que f5_tts)
    from f5_tts.api import F5TTS

    device = cfg.f5_device
    if device == "cuda":
        if not torch.cuda.is_available():
            print("  [voz-f5] AVISO: CUDA no disponible → usando CPU (será lento).")
            device = "cpu"
        else:
            print(f"  [voz-f5] GPU detectada: {torch.cuda.get_device_name(0)}")

    if not Path(cfg.f5_ckpt).exists():
        raise FileNotFoundError(
            f"No se encuentra el checkpoint de F5: {cfg.f5_ckpt}\n"
            "Descarga el modelo jpgallegoar/F5-Spanish (ver SETUP_VOZ_LOCAL.md)."
        )

    print(f"  [voz-f5] Cargando modelo F5 ({cfg.f5_model_arch})...")
    _f5_model = F5TTS(
        model=cfg.f5_model_arch,
        ckpt_file=cfg.f5_ckpt,
        vocab_file=cfg.f5_vocab,
        device=device,
    )
    print("  [voz-f5] Modelo listo.")
    return _f5_model


def text_to_speech(
    text: str,
    output_path: Path,
    voice_id: Optional[str] = None,   # aquí: ruta a una muestra de voz alternativa
    **_ignored,                        # acepta args de ElevenLabs sin romper
) -> Path:
    """
    Genera audio con tu voz clonada (F5) y lo guarda como .wav.
    `voice_id` puede ser la ruta a otra muestra de voz; si no, usa la del config.
    Si cambias la muestra, define F5_REF_TEXT con su transcripción exacta.
    """
    ref_sample = voice_id or cfg.f5_ref_sample
    if not Path(ref_sample).exists():
        raise FileNotFoundError(
            f"No se encuentra tu muestra de voz: {ref_sample}\n"
            "Graba tu voz y colócala ahí (ver SETUP_VOZ_LOCAL.md)."
        )

    model = _get_model()
    output_path = Path(output_path).with_suffix(".wav")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model.infer(
        ref_file=str(ref_sample),
        ref_text=cfg.f5_ref_text,
        gen_text=text,
        file_wave=str(output_path),
        remove_silence=True,
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

    _get_model()  # precarga antes del bucle

    audio_paths: list[Path] = []
    for i, segment in enumerate(segments):
        text = segment.get("text", "")
        if not text.strip():
            continue
        out_path = output_dir / f"segment_{i:03d}.wav"
        print(f"  [voz-f5] Segmento {i+1}/{len(segments)}: {text[:60]}...")
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
