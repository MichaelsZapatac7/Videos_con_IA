"""
YouTube Video Production Pipeline — CLI entry point.

Usage:
  python -m youtube_pipeline.main --topic "Los 5 mejores modelos de IA en 2026" --niche "tecnología"
  python -m youtube_pipeline.main --topic "..." --shorts
  python -m youtube_pipeline.main --help
"""

import argparse
import sys
import os
from pathlib import Path

# Allow running from the repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.generators.script_gen import generate_script, generate_shorts_from_long
from youtube_pipeline.generators.voiceover import generate_segment_voiceovers
from youtube_pipeline.generators.footage import fetch_segment_footage
from youtube_pipeline.editors.assembler import assemble_video


def check_env():
    """Validate required environment variables before running."""
    missing = []
    if not cfg.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")
    if not cfg.elevenlabs_api_key:
        missing.append("ELEVENLABS_API_KEY")
    if not cfg.pexels_api_key:
        missing.append("PEXELS_API_KEY")
    if missing:
        print(f"[error] Missing environment variables: {', '.join(missing)}")
        print("  Copy .env.example to .env and fill in your keys.")
        sys.exit(1)


def run_pipeline(
    topic: str,
    niche: str,
    language: str,
    duration: int,
    is_shorts: bool,
    style: str,
    output_dir: Path,
    music_path: Path | None,
    logo_path: Path | None,
    also_generate_shorts: bool,
):
    print(f"\n{'='*60}")
    print(f"  YouTube Pipeline — {cfg.channel_name}")
    print(f"{'='*60}")
    print(f"  Topic  : {topic}")
    print(f"  Niche  : {niche} | Lang: {language} | Shorts: {is_shorts}")
    print(f"{'='*60}\n")

    # ── 1. Generate script ──────────────────────────────────────────────────
    print("[1/4] Generating script with Claude...")
    script = generate_script(
        topic=topic,
        niche=niche,
        language=language,
        target_duration=duration,
        is_shorts=is_shorts,
        style=style,
    )
    print(f"  Title: {script.title}")
    print(f"  Segments: {len(script.segments)} | Est. duration: {script.total_estimated_seconds}s")

    job_dir = output_dir / "".join(c if c.isalnum() or c in "-_" else "_" for c in topic[:40])
    job_dir.mkdir(parents=True, exist_ok=True)

    # ── 2. Generate voiceovers ──────────────────────────────────────────────
    print("\n[2/4] Generating voiceovers with ElevenLabs...")
    audio_dir = job_dir / "audio"
    audio_dir.mkdir(exist_ok=True)
    audio_paths = generate_segment_voiceovers(script.segments, audio_dir)
    print(f"  {len(audio_paths)} audio files generated")

    # ── 3. Fetch stock footage ──────────────────────────────────────────────
    print("\n[3/4] Fetching footage from Pexels...")
    footage_dir = job_dir / "footage"
    footage_dir.mkdir(exist_ok=True)
    footage_paths = fetch_segment_footage(script.segments, footage_dir, is_shorts=is_shorts)
    found = sum(1 for p in footage_paths if p)
    print(f"  {found}/{len(footage_paths)} clips sourced")

    # ── 4. Assemble video ───────────────────────────────────────────────────
    print("\n[4/4] Assembling final video...")
    final_path = assemble_video(
        script=script,
        footage_paths=footage_paths,
        audio_paths=audio_paths,
        output_dir=job_dir,
        music_path=music_path,
        logo_path=logo_path,
        is_shorts=is_shorts,
        burn_captions=True,
    )

    # Print upload info
    print(f"\n{'='*60}")
    print(f"  READY TO UPLOAD")
    print(f"{'='*60}")
    print(f"  File   : {final_path}")
    print(f"  Title  : {script.title}")
    print(f"  Tags   : {', '.join(script.tags[:8])}")
    print(f"\n  Description (copy-paste):\n  {script.description}")
    print(f"{'='*60}\n")

    # Optionally generate companion Shorts from the long video
    if also_generate_shorts and not is_shorts:
        print("\n[bonus] Generating 3 YouTube Shorts from this video...")
        shorts = generate_shorts_from_long(script, num_shorts=3)
        for i, short_script in enumerate(shorts):
            print(f"\n  Short {i+1}: {short_script.title}")
            s_audio_dir = job_dir / f"shorts_{i}_audio"
            s_audio_dir.mkdir(exist_ok=True)
            s_audio = generate_segment_voiceovers(short_script.segments, s_audio_dir)
            s_footage_dir = job_dir / f"shorts_{i}_footage"
            s_footage_dir.mkdir(exist_ok=True)
            s_footage = fetch_segment_footage(short_script.segments, s_footage_dir, is_shorts=True)
            assemble_video(
                script=short_script,
                footage_paths=s_footage,
                audio_paths=s_audio,
                output_dir=job_dir / f"short_{i}",
                music_path=music_path,
                logo_path=logo_path,
                is_shorts=True,
            )

    return final_path


def main():
    parser = argparse.ArgumentParser(
        description="YouTube Video Production Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m youtube_pipeline.main --topic "GPT-5 vs Claude 4: cuál es mejor en 2026"
  python -m youtube_pipeline.main --topic "Cómo ganar dinero con IA en 2026" --niche "finanzas digitales" --shorts
  python -m youtube_pipeline.main --topic "Tutorial Python en 10 minutos" --lang en --duration 600
        """,
    )
    parser.add_argument("--topic", required=True, help="Video topic")
    parser.add_argument("--niche", default="tecnología e inteligencia artificial", help="Channel niche")
    parser.add_argument("--lang", default="es", help="Language code (es, en, ...)")
    parser.add_argument("--duration", type=int, default=480, help="Target duration in seconds")
    parser.add_argument("--shorts", action="store_true", help="Generate a YouTube Short (≤60s)")
    parser.add_argument("--style", default="educativo-entretenido", help="Video style")
    parser.add_argument("--output", default="output", help="Output directory")
    parser.add_argument("--music", default=None, help="Path to background music file")
    parser.add_argument("--logo", default=None, help="Path to channel logo/watermark PNG")
    parser.add_argument("--also-shorts", action="store_true", help="Also generate Shorts from long video")
    args = parser.parse_args()

    check_env()

    output_dir = Path(args.output)
    music_path = Path(args.music) if args.music else None
    logo_path = Path(args.logo) if args.logo else None

    run_pipeline(
        topic=args.topic,
        niche=args.niche,
        language=args.lang,
        duration=args.duration,
        is_shorts=args.shorts,
        style=args.style,
        output_dir=output_dir,
        music_path=music_path,
        logo_path=logo_path,
        also_generate_shorts=args.also_shorts,
    )


if __name__ == "__main__":
    main()
