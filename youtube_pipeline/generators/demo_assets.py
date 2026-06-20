"""
Generadores en MODO DEMO — funcionan SIN API keys externas.

- Voz: espeak-ng (TTS local, calidad robótica) en vez de ElevenLabs
- Footage: tarjetas de gradiente animado con el texto del cue, generadas con FFmpeg,
  en vez de stock real de Pexels

Sirve para probar el pipeline completo de extremo a extremo y producir un video
real que se pueda ver. Para calidad profesional, usa los generadores normales
(voiceover.py + footage.py) con tus API keys.
"""

import subprocess
import shutil
from pathlib import Path

from ..config import cfg


# Voz Piper (calidad casi natural) si el modelo está disponible; si no, espeak.
PIPER_VOICES_DIR = cfg.assets_dir / "piper_voices"
DEFAULT_PIPER_MODEL = PIPER_VOICES_DIR / "es-carlfm-x-low.onnx"


def _piper_available() -> bool:
    return shutil.which("piper") is not None and DEFAULT_PIPER_MODEL.exists()


def piper_voiceover(text: str, output_path: Path, model_path: Path = None) -> Path:
    """Genera voz con Piper TTS (local, calidad casi natural). Devuelve .wav."""
    model_path = model_path or DEFAULT_PIPER_MODEL
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path = output_path.with_suffix(".wav")
    subprocess.run(
        ["piper", "-m", str(model_path), "-f", str(wav_path)],
        input=text, text=True, check=True, capture_output=True,
    )
    return wav_path


def demo_voiceover(text: str, output_path: Path, voice: str = "es", speed: int = 155) -> Path:
    """Genera audio de voz con espeak-ng (local, sin key). Devuelve un .wav."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path = output_path.with_suffix(".wav")
    subprocess.run(
        ["espeak-ng", "-v", voice, "-s", str(speed), "-w", str(wav_path), text],
        check=True, capture_output=True,
    )
    return wav_path


def generate_demo_voiceovers(segments: list[dict], output_dir: Path) -> list[Path]:
    """
    Un archivo de voz por segmento. Usa Piper TTS si está disponible
    (mucho mejor), si no cae a espeak-ng.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    use_piper = _piper_available()
    engine = "Piper" if use_piper else "espeak"
    print(f"  [voz] Motor: {engine}")
    paths = []
    for i, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        if not text:
            continue
        out = output_dir / f"segment_{i:03d}.wav"
        print(f"  [{engine}] Segmento {i+1}/{len(segments)}")
        if use_piper:
            piper_voiceover(text, out)
        else:
            demo_voiceover(text, out)
        paths.append(out)
    return paths


# Paletas de color por índice para variar las tarjetas
_PALETTES = [
    ("0x1A1A2E", "0xFF6B35"),  # azul oscuro -> naranja
    ("0x0F3460", "0xE94560"),  # azul -> rojo
    ("0x16213E", "0x53A8B6"),  # azul -> cyan
    ("0x2D132C", "0xC72C41"),  # vino -> rojo
    ("0x0B0C10", "0x66FCF1"),  # negro -> cyan
    ("0x1B1B2F", "0x9D4EDD"),  # oscuro -> morado
    ("0x222831", "0xFFD369"),  # gris -> dorado
    ("0x14213D", "0xFCA311"),  # azul -> ambar
]


def _escape_drawtext(text: str) -> str:
    """Escapa texto para el filtro drawtext de FFmpeg."""
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "")
        .replace("%", "\\%")
        .replace(",", "\\,")
    )


def generate_demo_card(
    label: str,
    output_path: Path,
    duration: float,
    width: int,
    height: int,
    index: int = 0,
    font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
) -> Path:
    """
    Genera una tarjeta de video: gradiente de color + texto centrado del cue visual,
    con una sutil animación de zoom. Sustituye el stock footage en modo demo.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c1, c2 = _PALETTES[index % len(_PALETTES)]
    label_clean = _escape_drawtext(label.upper()[:40])

    # 'gradients' es un filtro fuente: se usa como input lavfi, no encadenado.
    gradient_src = (
        f"gradients=s={width}x{height}:c0={c1}:c1={c2}"
        f":x0=0:y0=0:x1={width}:y1={height}:d={duration}:r={cfg.video_fps}"
    )
    # etiqueta en el TERCIO SUPERIOR (los subtítulos van abajo) con leve flote
    vf = (
        f"drawtext=fontfile={font_path}:text='{label_clean}'"
        f":fontcolor=white:fontsize={int(height*0.055)}"
        f":x=(w-text_w)/2:y=h*0.28+12*sin(t)"
        f":box=1:boxcolor=black@0.40:boxborderw=22:line_spacing=12"
    )

    subprocess.run([
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", gradient_src,
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(output_path),
    ], check=True, capture_output=True)
    return output_path


def generate_demo_footage(
    segments: list[dict],
    output_dir: Path,
    is_shorts: bool = False,
) -> list[Path]:
    """Una tarjeta visual por segmento. Devuelve lista de paths."""
    output_dir.mkdir(parents=True, exist_ok=True)
    width = cfg.shorts_width if is_shorts else cfg.video_width
    height = cfg.shorts_height if is_shorts else cfg.video_height

    paths = []
    for i, seg in enumerate(segments):
        # Prefiere una etiqueta limpia si el guión la trae; si no, usa el cue
        label = seg.get("label") or " ".join(seg.get("visual_cue", "AI").split()[:4])
        dur = seg.get("duration_seconds", 10)
        out = output_dir / f"card_{i:03d}.mp4"
        print(f"  [demo-card] Segmento {i+1}/{len(segments)}: {label}")
        generate_demo_card(label, out, duration=dur + 4, width=width, height=height, index=i)
        paths.append(out)
    return paths


def check_demo_deps() -> dict:
    """Verifica que las dependencias del modo demo estén disponibles."""
    return {
        "ffmpeg": shutil.which("ffmpeg") is not None,
        "espeak-ng": shutil.which("espeak-ng") is not None,
    }
