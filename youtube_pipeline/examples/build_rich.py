"""
Construye el video ENRIQUECIDO con B-ROLL:
  - Bienvenida hablada del canal MZSHARD (intro con branding)
  - Cada IA se presenta con un MONTAJE: tarjeta de marca + varias tomas de apoyo
    (B-roll) de fotos reales de Pexels relevantes a esa IA, alternando cortes y
    movimiento Ken Burns para que el video NO se vea plano.
  - Outro de suscripción
  - Voz: ElevenLabs si hay red/keys; si no, Piper TTS local (fallback)

Ejecutar desde la raíz del repo:
  python -m youtube_pipeline.examples.build_rich
"""

import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.examples.script_7_ias import SCRIPT
from youtube_pipeline.generators.graphics import (
    make_support_image, make_welcome_image, make_outro_image, make_broll_image,
    PALETTES,
)
from youtube_pipeline.editors.video_editor import ken_burns
from youtube_pipeline.editors.assembler import assemble_video
from youtube_pipeline.editors.video_editor import concatenate_videos

# Narración de bienvenida del canal (se antepone al guión)
WELCOME_TEXT = (
    "¡Bienvenido a MZSHARD! Tu canal de inteligencia artificial y tecnología. "
    "Hoy te traigo un ranking que tienes que ver: las siete inteligencias "
    "artificiales más poderosas del momento. Vamos con ello."
)

# tagline + tipo de imagen por etiqueta del segmento
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

# Búsquedas de B-roll en Pexels por IA (varias para conseguir tomas distintas).
# Nota: Pexels es banco de fotos libres; no tiene logos de productos, así que
# usamos imágenes temáticas del DOMINIO de cada IA (lo más cercano y legal).
BROLL = {
    "WELCOME": [
        "artificial intelligence technology abstract", "futuristic digital network glowing",
    ],
    "LAS 7 IA MÁS PODEROSAS": [
        "artificial intelligence brain neural", "futuristic technology glowing blue",
        "digital data network particles",
    ],
    "1. FABLE 5": [
        "supercomputer data center servers", "glowing computer processor chip",
        "futuristic server room technology",
    ],
    "2. CLAUDE OPUS 4.8": [
        "programmer coding on screen", "software source code editor",
        "developer working laptop dark",
    ],
    "3. GPT-5": [
        "person chatting smartphone app", "chatbot conversation interface",
        "people using ai assistant phone",
    ],
    "4. GEMINI": [
        "multiple screens data analysis", "abstract data visualization colorful",
        "researcher analyzing information",
    ],
    "5. VIDEO IA: VEO & SORA": [
        "cinematic film camera production", "movie set dramatic lighting",
        "filmmaking scene cinema",
    ],
    "6. HIGGSFIELD": [
        "film director camera equipment", "professional cinema lens",
        "movie production crew set",
    ],
    "7. ELEVENLABS": [
        "microphone recording studio", "audio sound waveform glowing",
        "podcast studio recording",
    ],
    "SUSCRÍBETE": [],
}


def _blend_photo_card(card_path: Path, photo_path: Path, out_path: Path) -> Path:
    """
    Composita una foto real de Pexels como fondo suave detrás de la tarjeta de marca.
    La foto se oscurece (brillo 0.45) para que el texto siga legible y se mezcla
    al 38% foto + 62% tarjeta: la imagen real se ve a través del branding MZSHARD.
    """
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


def _collect_photos(queries: list[str], n: int, out_dir: Path, prefix: str) -> list[Path]:
    """
    Descarga hasta `n` fotos DISTINTAS de Pexels combinando varias búsquedas
    (round-robin) para conseguir variedad de tomas sobre la misma IA.
    """
    if not cfg.pexels_api_key or not queries:
        return []
    from youtube_pipeline.generators.footage import search_pexels_photos, download_photo
    buckets = []
    for q in queries:
        try:
            short_q = " ".join(q.split()[:5])
            buckets.append([p["url"] for p in search_pexels_photos(short_q, count=5) if p.get("url")])
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


def _segment_clip(shot_imgs: list[Path], dur: float, clip_out: Path, W, H, FPS) -> Path:
    """
    Convierte una lista de imágenes en UN clip de segmento: cada imagen recibe
    Ken Burns (alternando zoom in/out) y se concatenan. El montaje dura un poco
    más que el audio para que el ensamblador pueda recortarlo limpio.
    """
    n = max(1, len(shot_imgs))
    per = max(2.5, (dur + 1.0) / n)
    subclips = []
    for j, im in enumerate(shot_imgs):
        sc = clip_out.parent / f"{clip_out.stem}_{j}.mp4"
        ken_burns(im, sc, duration=per, width=W, height=H, fps=FPS,
                  direction="in" if j % 2 == 0 else "out")
        subclips.append(sc)
    if len(subclips) == 1:
        shutil.copy2(subclips[0], clip_out)
    else:
        concatenate_videos(subclips, clip_out)
    return clip_out


def main():
    print("=" * 60)
    print("  VIDEO ENRIQUECIDO CON B-ROLL — MZSHARD")
    print("=" * 60)

    job = cfg.output_dir / "rich_7_ias"
    (job / "audio").mkdir(parents=True, exist_ok=True)
    (job / "img").mkdir(parents=True, exist_ok=True)
    (job / "clips").mkdir(parents=True, exist_ok=True)

    W, H, FPS = cfg.video_width, cfg.video_height, cfg.video_fps

    segments = [{"text": WELCOME_TEXT, "label": "WELCOME"}] + SCRIPT.segments

    audio_paths, footage_paths, used_segments = [], [], []

    for i, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        label = seg.get("label", "")
        print(f"\n[{i+1}/{len(segments)}] {label or text[:30]}")

        # 1) voz
        audio = _gen_voice(text, job / "audio" / f"seg_{i:03d}")
        dur = _audio_dur(audio)
        print(f"    voz {dur:.1f}s -> {audio.name}")

        # 2) tarjeta de marca del segmento
        tagline, kind = TAGLINES.get(label, ("", "ai"))
        card_img = job / "img" / f"card_{i:03d}.png"
        if label == "WELCOME":
            make_welcome_image(card_img, channel="MZSHARD",
                               tagline="Inteligencia Artificial y Tecnología")
            disp_name = "MZSHARD"
        elif kind == "outro":
            make_outro_image(card_img, channel="MZSHARD")
            disp_name = "SUSCRÍBETE"
        elif kind == "topic":
            make_support_image("7", "LAS 7 IA", tagline, card_img, index=i)
            disp_name = "LAS 7 IA"
        else:
            num = label.split(".")[0].strip() if "." in label else str(i)
            disp_name = label.split(".", 1)[1].strip() if "." in label else label
            make_support_image(num.zfill(2), disp_name, tagline, card_img, index=i)

        # 3) Montaje con B-roll (las pantallas de marca quedan como toma única)
        is_branding = label in ("WELCOME", "SUSCRÍBETE")
        shot_imgs = [card_img]

        if not is_branding:
            n_shots = max(2, min(5, round(dur / 4.0)))
            photos = _collect_photos(BROLL.get(label, []), n_shots, job / "img", f"ph_{i:03d}")
            if photos:
                # Toma 0: tarjeta de marca mezclada con la primera foto
                shot_imgs = [_blend_photo_card(card_img, photos[0],
                                               job / "img" / f"shot_{i:03d}_0.png")]
                # Tomas siguientes: B-roll etiquetado con el nombre de la IA
                for j, ph in enumerate(photos[1:], start=1):
                    shot_imgs.append(make_broll_image(
                        ph, disp_name, job / "img" / f"shot_{i:03d}_{j}.png", index=i + j))
                print(f"    B-roll: {len(shot_imgs)} tomas (tarjeta + {len(shot_imgs)-1} fotos)")
            else:
                print(f"    sin fotos Pexels -> tarjeta única")

        # 4) Clip del segmento (montaje Ken Burns)
        clip = job / "clips" / f"clip_{i:03d}.mp4"
        _segment_clip(shot_imgs, dur, clip, W, H, FPS)

        audio_paths.append(audio)
        footage_paths.append(clip)
        used_segments.append({**seg, "duration_seconds": dur})

    rich_script = type(SCRIPT)(
        title=SCRIPT.title, description=SCRIPT.description, tags=SCRIPT.tags,
        hook=SCRIPT.hook, segments=used_segments,
        call_to_action=SCRIPT.call_to_action, thumbnail_text=SCRIPT.thumbnail_text,
        total_estimated_seconds=int(sum(s["duration_seconds"] for s in used_segments)),
        is_shorts=False,
    )

    print("\n[ensamblando] ...")
    final = assemble_video(
        script=rich_script, footage_paths=footage_paths, audio_paths=audio_paths,
        output_dir=job, is_shorts=False, burn_captions=True,
        add_title_card=False,
    )
    print(f"\n  LISTO -> {final}")
    return final


if __name__ == "__main__":
    main()
