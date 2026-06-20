"""
Construye el video DEMO "Las 7 IA más poderosas actualmente" SIN API keys.

Usa:
  - Guión: examples/script_7_ias.py (escrito directamente, no por API)
  - Voz: espeak-ng (local)
  - Footage: tarjetas de gradiente generadas con FFmpeg
  - Edición: el mismo assembler del pipeline real

Ejecutar desde la raíz del repo:
  python -m youtube_pipeline.examples.build_demo
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.examples.script_7_ias import SCRIPT
from youtube_pipeline.generators.demo_assets import (
    generate_demo_voiceovers, generate_demo_footage, check_demo_deps,
)
from youtube_pipeline.editors.assembler import assemble_video


def main():
    print("=" * 60)
    print("  DEMO — Las 7 IA más poderosas actualmente")
    print("  (sin API keys: voz local + tarjetas generadas)")
    print("=" * 60)

    deps = check_demo_deps()
    if not all(deps.values()):
        missing = [k for k, v in deps.items() if not v]
        print(f"[error] Faltan dependencias: {missing}")
        print("  Instala: sudo apt install ffmpeg espeak-ng")
        sys.exit(1)

    job_dir = cfg.output_dir / "demo_7_ias"
    job_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Generando voces (espeak-ng local)...")
    audio_paths = generate_demo_voiceovers(SCRIPT.segments, job_dir / "audio")

    print("\n[2/3] Generando footage (tarjetas FFmpeg)...")
    footage_paths = generate_demo_footage(SCRIPT.segments, job_dir / "footage")

    print("\n[3/3] Ensamblando video final...")
    final = assemble_video(
        script=SCRIPT,
        footage_paths=footage_paths,
        audio_paths=audio_paths,
        output_dir=job_dir,
        music_path=None,
        logo_path=None,
        is_shorts=False,
        burn_captions=True,
    )

    print("\n" + "=" * 60)
    print(f"  VIDEO DEMO LISTO: {final}")
    print("=" * 60)
    print(f"  Título : {SCRIPT.title}")
    print(f"  Tags   : {', '.join(SCRIPT.tags[:6])}...")
    print("\n  Esto es una DEMO con voz robótica y fondos simples.")
    print("  Con tus API keys (ElevenLabs + Pexels) se ve y suena profesional.")
    return final


if __name__ == "__main__":
    main()
