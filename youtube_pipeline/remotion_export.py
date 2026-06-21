"""
Exporta un trabajo ya renderizado (audio de ElevenLabs + fotos de Pexels) a un
MANIFEST para Remotion, copiando los assets a remotion/public/.

Así reutilizamos la voz y las fotos existentes (sin gastar cuota) y solo
cambiamos el MOTOR visual a Remotion, que da animaciones modernas.

Uso:
  python -m youtube_pipeline.remotion_export "<tema>" --plan-file <plan.json> --format full
  python -m youtube_pipeline.remotion_export "<tema>" --plan-file <plan.json> --format short

Imprime al final:  COMPOSITION=<id>  MANIFEST=<ruta>  FPS=<n>
"""

import sys
import re
import json
import shutil
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.create_video import _slug, _plan_to_segments, _short_segments
from youtube_pipeline.generators.graphics import PALETTES

REMOTION = Path(__file__).parent.parent / "remotion"
PUBLIC = REMOTION / "public"
MANIFESTS = REMOTION / "manifests"

CODE_RE = re.compile(
    r"[()*=]|SELECT|FROM|GROUP|JOIN|CASE|OVER|QUALIFY|COUNT|SUM|AVG|DATE_TRUNC|ROW_NUMBER|PARTITION",
    re.I,
)


def _dur_frames(audio: Path, fps: int) -> int:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(audio)], capture_output=True, text=True)
    try:
        return max(1, round(float(r.stdout.strip()) * fps))
    except ValueError:
        return 6 * fps


def export(topic: str, plan: dict, fmt: str, canal: str = "MZSHARD") -> tuple[str, Path, int]:
    fps = cfg.video_fps
    slug = _slug(topic)
    out_root = cfg.output_dir / slug

    if fmt == "short":
        built = _short_segments(plan, topic)
        if not built:
            raise SystemExit("El plan no tiene sección 'short'.")
        segments, _ = built
        job = out_root / "short"
        comp = "Short"
    else:
        segments, _ = _plan_to_segments(plan, topic, canal)
        job = out_root / "completo"
        comp = "Video"

    audio_dir = job / "audio"
    img_dir = job / "img"
    if not audio_dir.exists():
        raise SystemExit(f"No existe el audio en {audio_dir}. Genera primero el video base.")

    asset_dir_name = f"{slug[:24]}_{fmt}"
    dest = PUBLIC / asset_dir_name
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    manifest_segs = []
    for i, seg in enumerate(segments):
        kind = seg.get("kind", "item")
        # audio
        a = audio_dir / f"seg_{i:03d}.mp3"
        if not a.exists():
            a = audio_dir / f"seg_{i:03d}.wav"
        audio_rel = None
        if a.exists():
            shutil.copy2(a, dest / a.name)
            audio_rel = f"{asset_dir_name}/{a.name}"
        frames = _dur_frames(a, fps) if a.exists() else 6 * fps
        # imágenes (B-roll real de Pexels)
        imgs = sorted(img_dir.glob(f"ph_{i:03d}_*.jpg"))
        img_rels = []
        for ph in imgs:
            shutil.copy2(ph, dest / ph.name)
            img_rels.append(f"{asset_dir_name}/{ph.name}")
        tagline = seg.get("tagline", "") or ""
        accent = list(PALETTES[i % len(PALETTES)][1])
        manifest_segs.append({
            "kind": kind,
            "title": seg.get("label", ""),
            "number": seg.get("number", "") or "",
            "tagline": tagline,
            "code": bool(tagline and CODE_RE.search(tagline)),
            "text": seg.get("text", "") or "",
            "audio": audio_rel,
            "durationInFrames": frames,
            "images": img_rels,
            "accent": accent,
        })

    # música (cama sintetizada o Mureka, si existe)
    music_rel = None
    for cand in (out_root / "music_bed.wav", out_root / "mureka_music.mp3"):
        if cand.exists():
            shutil.copy2(cand, dest / cand.name)
            music_rel = f"{asset_dir_name}/{cand.name}"
            break

    manifest = {"fps": fps, "channel": canal, "music": music_rel, "segments": manifest_segs}
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    mpath = MANIFESTS / f"{asset_dir_name}.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return comp, mpath, fps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tema")
    ap.add_argument("--plan-file", required=True)
    ap.add_argument("--format", choices=["full", "short"], default="full")
    ap.add_argument("--canal", default="MZSHARD")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
    comp, mpath, fps = export(args.tema, plan, args.format, args.canal)
    total = sum(s["durationInFrames"] for s in json.loads(mpath.read_text())["segments"])
    print(f"COMPOSITION={comp}")
    print(f"MANIFEST={mpath}")
    print(f"FPS={fps}")
    print(f"SEGMENTS={len(json.loads(mpath.read_text())['segments'])} FRAMES={total} (~{total/fps:.0f}s)")


if __name__ == "__main__":
    main()
