"""
Renderizador de VIDEO ENRIQUECIDO CON B-ROLL (reutilizable).

Expone `render_video(segments, meta, job_dir)` que produce el video final a
partir de una lista de segmentos ya descritos (texto, tarjeta, tagline y
búsquedas de B-roll). Lo usan:
  - build_rich.main()        -> el ejemplo fijo de "Las 7 IA más poderosas"
  - youtube_pipeline.create_video -> cualquier tema que tú indiques

Cada segmento es un dict con:
  text   : narración (voz)
  kind   : "welcome" | "topic" | "item" | "outro"
  label  : título que va en la tarjeta y como etiqueta del B-roll
  number : "01".. para items (o "" / None)
  tagline: subtítulo corto de la tarjeta
  broll  : lista de búsquedas de fotos en Pexels (inglés). Vacío => tarjeta sola

Voz: ElevenLabs si hay key; si no, Piper TTS local (fallback).
Ejecutar el ejemplo desde la raíz del repo:
  python -m youtube_pipeline.examples.build_rich
"""

import sys
import shutil
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.examples.script_7_ias import SCRIPT
from youtube_pipeline.generators.graphics import (
    make_support_image, make_welcome_image, make_outro_image, make_broll_image,
)
from youtube_pipeline.editors.video_editor import ken_burns, concatenate_videos
from youtube_pipeline.editors.assembler import assemble_video

# Narración de bienvenida por defecto del canal
DEFAULT_WELCOME = (
    "¡Bienvenido a MZSHARD! Tu canal de inteligencia artificial y tecnología. "
    "Quédate hasta el final porque esto te va a interesar. Vamos con ello."
)


# ── helpers de imagen / audio ───────────────────────────────────────────────

def _blend_photo_card(card_path: Path, photo_path: Path, out_path: Path) -> Path:
    """Composita una foto real de Pexels como fondo suave detrás de la tarjeta."""
    from PIL import Image, ImageEnhance
    card = Image.open(card_path).convert("RGB")
    W, H = card.size
    photo = Image.open(photo_path).convert("RGB")
    pw, ph = photo.size
    card_ratio = W / H
    if pw / ph > card_ratio:
        new_w = int(ph * card_ratio)
        photo = photo.crop(((pw - new_w) // 2, 0, (pw + new_w) // 2, ph))
    else:
        new_h = int(pw / card_ratio)
        photo = photo.crop((0, (ph - new_h) // 2, pw, (ph + new_h) // 2))
    photo = photo.resize((W, H), Image.LANCZOS)
    photo_dark = ImageEnhance.Brightness(photo).enhance(0.45)
    result = Image.blend(photo_dark, card, alpha=0.62)
    result.save(out_path, quality=95)
    return out_path


def _audio_dur(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 6.0


def _gen_voice(text: str, out: Path):
    """ElevenLabs si está disponible; si no, Piper local."""
    try:
        from youtube_pipeline.generators.voiceover import text_to_speech
        if cfg.elevenlabs_api_key:
            return text_to_speech(text, out.with_suffix(".mp3"), voice_id=cfg.elevenlabs_voice_id)
    except Exception as e:
        print(f"    [voz] ElevenLabs no disponible ({str(e)[:50]}), uso Piper")
    from youtube_pipeline.generators.demo_assets import piper_voiceover, demo_voiceover, _piper_available
    return piper_voiceover(text, out) if _piper_available() else demo_voiceover(text, out)


def _collect_photos(queries: list[str], n: int, out_dir: Path, prefix: str,
                    orientation: str = "landscape") -> list[Path]:
    """Descarga hasta n fotos DISTINTAS de Pexels combinando varias búsquedas (round-robin)."""
    if not cfg.pexels_api_key or not queries:
        return []
    from youtube_pipeline.generators.footage import search_pexels_photos, download_photo
    buckets = []
    for q in queries:
        try:
            short_q = " ".join(q.split()[:5])
            buckets.append([p["url"] for p in search_pexels_photos(short_q, count=5, orientation=orientation) if p.get("url")])
        except Exception as e:
            print(f"    [pexels] {str(e)[:60]}")
            buckets.append([])

    urls, seen, idx = [], set(), 0
    while len(urls) < n and any(idx < len(b) for b in buckets):
        for b in buckets:
            if idx < len(b) and b[idx] not in seen:
                seen.add(b[idx])
                urls.append(b[idx])
                if len(urls) >= n:
                    break
        idx += 1

    paths = []
    for k, u in enumerate(urls):
        try:
            paths.append(download_photo(u, out_dir / f"{prefix}_{k}.jpg"))
        except Exception as e:
            print(f"    [pexels descarga] {str(e)[:60]}")
    return paths


def _xfade_concat(subclips: list[Path], per: float, out_path: Path, t: float = 0.5) -> Path:
    """Une subclips con crossfade (transición animada). Si falla, concatena duro."""
    n = len(subclips)
    inputs = []
    for sc in subclips:
        inputs += ["-i", str(sc)]
    # Cadena de xfade encadenada: offset_k = k*(per - t)
    chains, prev = [], "[0:v]"
    for k in range(1, n):
        offset = k * (per - t)
        out_lbl = f"[v{k}]" if k < n - 1 else "[vout]"
        chains.append(f"{prev}[{k}:v]xfade=transition=fade:duration={t}:offset={offset:.3f}{out_lbl}")
        prev = out_lbl
    filt = ";".join(chains)
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", filt,
           "-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(out_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    [xfade] fallo, uso concat duro: {r.stderr[-160:]}")
        concatenate_videos(subclips, out_path)
    return out_path


def _segment_clip(shot_imgs: list[Path], dur: float, clip_out: Path, W, H, FPS) -> Path:
    """Convierte una lista de imágenes en UN clip: cada imagen con Ken Burns + crossfades."""
    n = max(1, len(shot_imgs))
    t = 0.5  # duración del crossfade
    # Compensa el tiempo perdido en las transiciones para cubrir el audio
    per = max(2.5, (dur + 1.0 + (n - 1) * t) / n)
    subclips = []
    for j, im in enumerate(shot_imgs):
        sc = clip_out.parent / f"{clip_out.stem}_{j}.mp4"
        ken_burns(im, sc, duration=per, width=W, height=H, fps=FPS,
                  direction="in" if j % 2 == 0 else "out")
        subclips.append(sc)
    if len(subclips) == 1:
        shutil.copy2(subclips[0], clip_out)
    else:
        _xfade_concat(subclips, per, clip_out, t=t)
    return clip_out


# ── renderizador principal ──────────────────────────────────────────────────

def render_video(segments: list[dict], meta: dict, job_dir: Path, channel: str = "MZSHARD",
                 is_shorts: bool = False, music_path: Path | None = None) -> Path:
    """
    Produce el video final a partir de `segments` (ver formato en el docstring
    del módulo). `meta` aporta title/description/tags/thumbnail_text para el
    ensamblado y los subtítulos.

    is_shorts : si True, renderiza vertical 9:16 (Shorts/Reel/TikTok).
    music_path: cama de música opcional bajo la voz. Devuelve la ruta del MP4.
    """
    fmt = "SHORT 9:16" if is_shorts else "16:9"
    print("=" * 60)
    print(f"  VIDEO ENRIQUECIDO CON B-ROLL ({fmt}) — {channel}")
    print(f"  {meta.get('title', '')}")
    print("=" * 60)

    (job_dir / "audio").mkdir(parents=True, exist_ok=True)
    (job_dir / "img").mkdir(parents=True, exist_ok=True)
    (job_dir / "clips").mkdir(parents=True, exist_ok=True)
    if is_shorts:
        W, H = cfg.shorts_width, cfg.shorts_height
    else:
        W, H = cfg.video_width, cfg.video_height
    FPS = cfg.video_fps
    orientation = "portrait" if is_shorts else "landscape"

    audio_paths, footage_paths, used_segments = [], [], []

    for i, seg in enumerate(segments):
        text = (seg.get("text") or "").strip()
        kind = seg.get("kind", "item")
        label = seg.get("label", "")
        number = seg.get("number") or ""
        tagline = seg.get("tagline", "")
        broll = seg.get("broll") or []
        print(f"\n[{i+1}/{len(segments)}] {kind.upper()} · {label[:30]}")

        # 1) voz
        audio = _gen_voice(text, job_dir / "audio" / f"seg_{i:03d}")
        dur = _audio_dur(audio)
        print(f"    voz {dur:.1f}s -> {audio.name}")

        # 2) tarjeta de marca del segmento según su tipo
        card_img = job_dir / "img" / f"card_{i:03d}.png"
        if kind == "welcome":
            make_welcome_image(card_img, channel=channel,
                               tagline=tagline or "Inteligencia Artificial y Tecnología",
                               width=W, height=H)
        elif kind == "outro":
            make_outro_image(card_img, channel=channel, width=W, height=H)
        else:  # topic / item
            make_support_image(str(number), label, tagline, card_img, index=i, width=W, height=H)
        disp_name = channel if kind == "welcome" else (label or channel)

        # 3) montaje con B-roll (welcome/outro quedan como toma única de marca)
        shot_imgs = [card_img]
        if kind in ("topic", "item") and broll:
            n_shots = max(2, min(5, round(dur / 4.0)))
            photos = _collect_photos(broll, n_shots, job_dir / "img", f"ph_{i:03d}",
                                     orientation=orientation)
            if photos:
                shot_imgs = [_blend_photo_card(card_img, photos[0],
                                               job_dir / "img" / f"shot_{i:03d}_0.png")]
                for j, ph in enumerate(photos[1:], start=1):
                    shot_imgs.append(make_broll_image(
                        ph, disp_name, job_dir / "img" / f"shot_{i:03d}_{j}.png",
                        index=i + j, width=W, height=H))
                print(f"    B-roll: {len(shot_imgs)} tomas")
            else:
                print(f"    sin fotos Pexels -> tarjeta única")

        # 4) clip del segmento
        clip = job_dir / "clips" / f"clip_{i:03d}.mp4"
        _segment_clip(shot_imgs, dur, clip, W, H, FPS)

        audio_paths.append(audio)
        footage_paths.append(clip)
        used_segments.append({"text": text, "label": label, "duration_seconds": dur})

    # Ensamblar
    script = type(SCRIPT)(
        title=meta.get("title", "Video"),
        description=meta.get("description", ""),
        tags=meta.get("tags", []),
        hook=meta.get("hook", ""),
        segments=used_segments,
        call_to_action=meta.get("call_to_action", ""),
        thumbnail_text=meta.get("thumbnail_text", ""),
        total_estimated_seconds=int(sum(s["duration_seconds"] for s in used_segments)),
        is_shorts=is_shorts,
    )

    print("\n[ensamblando] ...")
    final = assemble_video(
        script=script, footage_paths=footage_paths, audio_paths=audio_paths,
        output_dir=job_dir, is_shorts=is_shorts, burn_captions=True,
        add_title_card=False, music_path=music_path,
    )
    print(f"\n  LISTO -> {final}")
    return final


# ── ejemplo fijo: "Las 7 IA más poderosas" ──────────────────────────────────

# tagline por etiqueta del segmento del ejemplo
TAGLINES = {
    "LAS 7 IA MÁS PODEROSAS": ("RANKING 2026", "topic"),
    "1. FABLE 5": ("El modelo más potente — con límites de uso", "ai"),
    "2. CLAUDE OPUS 4.8": ("Rey de la programación y los agentes", "ai"),
    "3. GPT-5": ("El todoterreno que todos conocen", "ai"),
    "4. GEMINI": ("Contexto gigante y multimodal", "ai"),
    "5. VIDEO IA: VEO & SORA": ("Texto a video cinematográfico", "ai"),
    "6. HIGGSFIELD": ("Tu director de cine con IA", "ai"),
    "7. ELEVENLABS": ("La voz más realista del mundo", "ai"),
    "SUSCRÍBETE": ("", "outro"),
}

BROLL = {
    "LAS 7 IA MÁS PODEROSAS": ["artificial intelligence brain neural", "futuristic technology glowing blue", "digital data network particles"],
    "1. FABLE 5": ["supercomputer data center servers", "glowing computer processor chip", "futuristic server room technology"],
    "2. CLAUDE OPUS 4.8": ["programmer coding on screen", "software source code editor", "developer working laptop dark"],
    "3. GPT-5": ["person chatting smartphone app", "chatbot conversation interface", "people using ai assistant phone"],
    "4. GEMINI": ["multiple screens data analysis", "abstract data visualization colorful", "researcher analyzing information"],
    "5. VIDEO IA: VEO & SORA": ["cinematic film camera production", "movie set dramatic lighting", "filmmaking scene cinema"],
    "6. HIGGSFIELD": ["film director camera equipment", "professional cinema lens", "movie production crew set"],
    "7. ELEVENLABS": ["microphone recording studio", "audio sound waveform glowing", "podcast studio recording"],
}


def main():
    """Construye el ejemplo fijo de las 7 IA usando el renderizador genérico."""
    welcome_text = (
        "¡Bienvenido a MZSHARD! Tu canal de inteligencia artificial y tecnología. "
        "Hoy te traigo un ranking que tienes que ver: las siete inteligencias "
        "artificiales más poderosas del momento. Vamos con ello."
    )
    segments = [{
        "text": welcome_text, "kind": "welcome", "label": "MZSHARD",
        "tagline": "Inteligencia Artificial y Tecnología", "broll": [],
    }]

    for seg in SCRIPT.segments:
        label = seg["label"]
        tagline, kind_tag = TAGLINES.get(label, ("", "ai"))
        if kind_tag == "topic":
            segments.append({"text": seg["text"], "kind": "topic", "label": "LAS 7 IA",
                             "number": "7", "tagline": tagline, "broll": BROLL.get(label, [])})
        elif kind_tag == "outro":
            segments.append({"text": seg["text"], "kind": "outro", "label": "SUSCRÍBETE", "broll": []})
        else:
            num = label.split(".")[0].strip()
            name = label.split(".", 1)[1].strip()
            segments.append({"text": seg["text"], "kind": "item", "label": name,
                             "number": num.zfill(2), "tagline": tagline, "broll": BROLL.get(label, [])})

    meta = {
        "title": SCRIPT.title, "description": SCRIPT.description, "tags": SCRIPT.tags,
        "hook": SCRIPT.hook, "call_to_action": SCRIPT.call_to_action,
        "thumbnail_text": SCRIPT.thumbnail_text,
    }
    return render_video(segments, meta, cfg.output_dir / "rich_7_ias", channel="MZSHARD")


if __name__ == "__main__":
    main()
