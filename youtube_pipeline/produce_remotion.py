"""
Pipeline UNIFICADO con motor Remotion (un solo comando por tema).

Pasos:
  1) genera voz (ElevenLabs, fallback Piper) e imágenes B-roll (Pexels) por segmento
     -> SIN el render viejo de ffmpeg (ahorra ~40 min por video)
  2) exporta los manifests (full 16:9 + short 9:16) con música de biblioteca y logo
  3) renderiza ambos con Remotion (animado)
  4) comprime las entregas a entregas/<base>_COMPLETO_ANIMADO.mp4 y _SHORT_ANIMADO.mp4

Uso:
  python -m youtube_pipeline.produce_remotion "<tema>" --plan-file <plan.json> --out-base <Nombre>
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.create_video import _plan_to_segments, _short_segments, _slug
from youtube_pipeline.examples.build_rich import _gen_voice, _collect_photos, _audio_dur
from youtube_pipeline import remotion_export as rx

REMOTION = Path(__file__).parent.parent / "remotion"
ENTREGAS = Path(__file__).parent.parent / "entregas"


class QuotaError(RuntimeError):
    """ElevenLabs sin cuota: detener el batch y avisar."""


def _voice_strict(text: str, out_base: Path) -> Path:
    """Voz SOLO con ElevenLabs (sin fallback a Piper). Lanza QuotaError si falla."""
    from youtube_pipeline.generators.voiceover import text_to_speech
    try:
        return text_to_speech(text, out_base.with_suffix(".mp3"), voice_id=cfg.elevenlabs_voice_id)
    except Exception as e:
        raise QuotaError(f"ElevenLabs no disponible: {str(e)[:120]}")


def _prepare(segments: list[dict], job_dir: Path, is_shorts: bool):
    """Genera voz + imágenes B-roll por segmento (sin render). Reanudable."""
    (job_dir / "audio").mkdir(parents=True, exist_ok=True)
    (job_dir / "img").mkdir(parents=True, exist_ok=True)
    orient = "portrait" if is_shorts else "landscape"
    max_shots = 3 if is_shorts else 5
    for i, seg in enumerate(segments):
        text = (seg.get("text") or "").strip()
        mp3 = job_dir / "audio" / f"seg_{i:03d}.mp3"
        if mp3.exists() and mp3.stat().st_size > 1024:
            audio = mp3  # reanudar: ya existe
        else:
            audio = _voice_strict(text, job_dir / "audio" / f"seg_{i:03d}")
        dur = _audio_dur(audio)
        print(f"    [{i+1}/{len(segments)}] {seg.get('kind')} voz {dur:.0f}s", flush=True)
        if seg.get("kind") in ("topic", "item") and seg.get("broll"):
            if (job_dir / "img" / f"ph_{i:03d}_0.jpg").exists():
                continue  # reanudar: imágenes ya descargadas
            n = max(2, min(max_shots, round(dur / 4.0)))
            _collect_photos(seg["broll"], n, job_dir / "img", f"ph_{i:03d}", orientation=orient)


def _render(comp: str, manifest: Path, out: Path):
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out),
           f"--props={manifest}", "--concurrency=4", "--log=error"]
    print(f"  [remotion] {comp} -> {out.name}", flush=True)
    r = subprocess.run(cmd, cwd=str(REMOTION))
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"Remotion render falló para {comp}")


def _compress(src: Path, dst: Path, crf: int = 26):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(dst),
    ], check=True, capture_output=True)


def produce(topic: str, plan: dict, out_base: str, canal: str = "MZSHARD",
            music: str | None = None, do_short: bool = True):
    slug = _slug(topic)
    out_root = cfg.output_dir / slug

    # 1) preparar assets
    full_segs, _ = _plan_to_segments(plan, topic, canal)
    print(f"\n== {out_base}: preparando VOZ+IMÁGENES (completo, {len(full_segs)} seg) ==", flush=True)
    _prepare(full_segs, out_root / "completo", is_shorts=False)

    short_built = _short_segments(plan, topic)
    if do_short and short_built:
        s_segs, _ = short_built
        print(f"== {out_base}: preparando VOZ+IMÁGENES (short, {len(s_segs)} seg) ==", flush=True)
        _prepare(s_segs, out_root / "short", is_shorts=True)

    # 2) exportar manifests
    comp_f, man_f, fps = rx.export(topic, plan, "full", canal, music_name=music)
    tmp_full = Path("/tmp") / f"{out_base}_full.mp4"
    _render(comp_f, man_f, tmp_full)
    out_full = ENTREGAS / f"{out_base}_COMPLETO_ANIMADO.mp4"
    _compress(tmp_full, out_full)
    print(f"  ✓ {out_full.name} ({out_full.stat().st_size//1048576} MB)", flush=True)

    out_short = None
    if do_short and short_built:
        comp_s, man_s, _ = rx.export(topic, plan, "short", canal, music_name=music)
        tmp_short = Path("/tmp") / f"{out_base}_short.mp4"
        _render(comp_s, man_s, tmp_short)
        out_short = ENTREGAS / f"{out_base}_SHORT_ANIMADO.mp4"
        _compress(tmp_short, out_short)
        print(f"  ✓ {out_short.name} ({out_short.stat().st_size//1048576} MB)", flush=True)

    return out_full, out_short


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tema")
    ap.add_argument("--plan-file", required=True)
    ap.add_argument("--out-base", required=True)
    ap.add_argument("--canal", default="MZSHARD")
    ap.add_argument("--music", default=None)
    ap.add_argument("--no-short", action="store_true")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
    f, s = produce(args.tema, plan, args.out_base, canal=args.canal,
                   music=args.music, do_short=not args.no_short)
    print(f"\nDONE base={args.out_base}\n  full={f}\n  short={s}")


if __name__ == "__main__":
    main()
