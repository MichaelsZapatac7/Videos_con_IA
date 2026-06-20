"""
Construye el video PROFESIONAL "Las 7 IA más poderosas" con APIs reales:
  - Voz: ElevenLabs (voz humana, voice_id del .env)
  - Footage: Pexels (stock HD real) según el visual_cue de cada segmento
  - Edición: el assembler del pipeline

Requiere que el entorno tenga acceso de red a api.elevenlabs.io y *.pexels.com,
y las keys en youtube_pipeline/.env

Ejecutar desde la raíz del repo:
  python -m youtube_pipeline.examples.build_full
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.examples.script_7_ias import SCRIPT
from youtube_pipeline.generators.voiceover import generate_segment_voiceovers
from youtube_pipeline.generators.footage import fetch_segment_footage
from youtube_pipeline.editors.assembler import assemble_video


def main():
    print("=" * 60)
    print("  PRODUCCIÓN FULL — Las 7 IA más poderosas")
    print("  (ElevenLabs voz real + Pexels footage HD)")
    print("=" * 60)

    job_dir = cfg.output_dir / "full_7_ias"
    job_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Generando voces con ElevenLabs...")
    audio_paths = generate_segment_voiceovers(
        SCRIPT.segments, job_dir / "audio", voice_id=cfg.elevenlabs_voice_id
    )
    print(f"  {len(audio_paths)} voces generadas")

    print("\n[2/3] Descargando footage HD de Pexels...")
    footage_paths = fetch_segment_footage(
        SCRIPT.segments, job_dir / "footage", is_shorts=False
    )
    found = sum(1 for p in footage_paths if p)
    print(f"  {found}/{len(footage_paths)} clips descargados")

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
    print(f"  VIDEO PROFESIONAL LISTO: {final}")
    print("=" * 60)
    print(f"  Título      : {SCRIPT.title}")
    print(f"  Descripción : {SCRIPT.description}")
    print(f"  Tags        : {', '.join(SCRIPT.tags)}")
    return final


if __name__ == "__main__":
    main()
