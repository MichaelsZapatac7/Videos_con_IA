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
MEDIA = Path(__file__).parent.parent / "media"
AUDIO_EXT = (".mp3", ".wav", ".m4a", ".ogg")
IMG_EXT = (".png", ".webp", ".jpg", ".jpeg")


def _pick_music(slug: str, fmt: str, music_name: str | None) -> Path | None:
    """Elige una pista de media/music: por nombre, o rotando de forma estable."""
    mdir = MEDIA / "music"
    tracks = sorted(p for p in mdir.glob("*") if p.suffix.lower() in AUDIO_EXT) if mdir.exists() else []
    if not tracks:
        return None
    if music_name:
        for t in tracks:
            if t.stem.lower() == music_name.lower():
                return t
    idx = sum(ord(c) for c in (slug + fmt)) % len(tracks)
    return tracks[idx]


def _pick_logo() -> Path | None:
    ldir = MEDIA / "logo"
    if ldir.exists():
        for p in sorted(ldir.glob("*")):
            if p.suffix.lower() in IMG_EXT:
                return p
    return None

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


def export(topic: str, plan: dict, fmt: str, canal: str = "MZSHARD",
           music_name: str | None = None) -> tuple[str, Path, int]:
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

    # música: biblioteca media/music (prioridad) -> cama sintetizada/Mureka
    music_rel = None
    track = _pick_music(slug, fmt, music_name)
    if track is None:
        for cand in (out_root / "music_bed.wav", out_root / "mureka_music.mp3"):
            if cand.exists():
                track = cand
                break
    if track is not None:
        shutil.copy2(track, dest / track.name)
        music_rel = f"{asset_dir_name}/{track.name}"
        print(f"  música: {track.name}")

    # logo (marca de agua) desde media/logo
    logo_rel = None
    logo = _pick_logo()
    if logo is not None:
        shutil.copy2(logo, dest / logo.name)
        logo_rel = f"{asset_dir_name}/{logo.name}"
        print(f"  logo: {logo.name}")

    manifest = {"fps": fps, "channel": canal, "music": music_rel,
                "logo": logo_rel, "segments": manifest_segs}
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
    ap.add_argument("--music", default=None, help="Nombre de pista en media/music (sin extensión)")
    args = ap.parse_args()
    plan = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))
    comp, mpath, fps = export(args.tema, plan, args.format, args.canal, music_name=args.music)
    total = sum(s["durationInFrames"] for s in json.loads(mpath.read_text())["segments"])
    print(f"COMPOSITION={comp}")
    print(f"MANIFEST={mpath}")
    print(f"FPS={fps}")
    print(f"SEGMENTS={len(json.loads(mpath.read_text())['segments'])} FRAMES={total} (~{total/fps:.0f}s)")


if __name__ == "__main__":
    main()
