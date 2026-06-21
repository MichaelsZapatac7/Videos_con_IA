"""
Pipeline de UN COMANDO por TEMA.

Tú das un tema y se genera el video completo (guion con Claude + voz ElevenLabs
+ B-roll de Pexels + diseño MZSHARD + subtítulos), reutilizando el renderizador
de examples.build_rich.

Uso:
  python -m youtube_pipeline.create_video "Los 7 riesgos de usar IA en 2026"
  python -m youtube_pipeline.create_video "Las 5 mejores apps de IA" --canal MZSHARD --idioma es

O desde código:
  from youtube_pipeline.create_video import crear_video
  crear_video("Los 7 riesgos de usar IA en 2026")
"""

import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_pipeline.config import cfg
from youtube_pipeline.generators.script_gen import generate_video_plan
from youtube_pipeline.generators.music import generate_music_bed
from youtube_pipeline.examples.build_rich import render_video, DEFAULT_WELCOME


def _slug(text: str, n: int = 40) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text[:n]).strip("_") or "video"


def _plan_to_segments(plan: dict, topic: str, channel: str) -> tuple[list[dict], dict]:
    """Convierte el plan de Claude en la lista de segmentos que espera render_video."""
    intro_card = plan.get("intro_card") or plan.get("thumbnail_text") or topic
    welcome_text = (
        f"¡Bienvenido a {channel}! Tu canal de inteligencia artificial y tecnología. "
        f"Hoy hablamos de {topic.lower()}. Quédate hasta el final. Vamos con ello."
    ) if channel else DEFAULT_WELCOME

    segments = [{
        "text": welcome_text, "kind": "welcome", "label": channel,
        "tagline": "Inteligencia Artificial y Tecnología", "broll": [],
    }]

    # Intro / hook como tarjeta de tema
    segments.append({
        "text": plan.get("intro_text", ""), "kind": "topic", "label": intro_card,
        "number": "", "tagline": plan.get("title", ""),
        "broll": plan.get("intro_broll") or [],
    })

    # Items numerados
    items = plan.get("items", [])
    for i, item in enumerate(items, start=1):
        segments.append({
            "text": item.get("text", ""), "kind": "item",
            "label": item.get("title", f"Punto {i}"),
            "number": f"{i:02d}", "tagline": item.get("tagline", ""),
            "broll": item.get("broll") or [],
        })

    # Outro
    segments.append({
        "text": plan.get("outro_text", "Suscríbete al canal para no perderte el próximo video."),
        "kind": "outro", "label": "SUSCRÍBETE", "broll": [],
    })

    meta = {
        "title": plan.get("title", topic),
        "description": plan.get("description", ""),
        "tags": plan.get("tags", []),
        "thumbnail_text": plan.get("thumbnail_text", ""),
        "hook": plan.get("intro_text", ""),
        "call_to_action": plan.get("outro_text", ""),
    }
    return segments, meta


def _short_segments(plan: dict, topic: str) -> tuple[list[dict], dict] | None:
    """
    Construye los segmentos del SHORT (vertical) a partir de plan["short"].
    El Short es rápido: gancho + 2-3 puntos clave + CTA "mira el video completo".
    Devuelve None si el plan no trae sección short.
    """
    short = plan.get("short")
    if not short:
        return None

    segments = [{
        "text": short.get("hook_text", ""), "kind": "topic",
        "label": short.get("hook_card") or plan.get("thumbnail_text", topic),
        "number": "", "tagline": "", "broll": short.get("hook_broll") or [],
    }]
    for i, pt in enumerate(short.get("points", []), start=1):
        segments.append({
            "text": pt.get("text", ""), "kind": "item",
            "label": pt.get("title", f"Tip {i}"), "number": f"{i:02d}",
            "tagline": pt.get("tagline", ""), "broll": pt.get("broll") or [],
        })
    segments.append({
        "text": short.get("cta_text", "Mira el video completo en el canal. Te espero."),
        "kind": "outro", "label": "VE EL VIDEO", "broll": [],
    })

    meta = {
        "title": (plan.get("title", topic) + " #shorts"),
        "description": plan.get("description", ""),
        "tags": (plan.get("tags", []) + ["shorts", "reel", "tiktok"]),
        "thumbnail_text": plan.get("thumbnail_text", ""),
    }
    return segments, meta


def _resolve_music(job_dir: Path, topic: str = "") -> Path | None:
    """
    Resuelve la música de fondo en este orden de prioridad:
      1) un archivo en youtube_pipeline/assets/music (lo que dejes tú manda)
      2) Mureka.ai (si hay MUREKA_API_KEY) — instrumental generado por IA
      3) cama ambiental sintetizada con FFmpeg (respaldo offline)
    """
    music_dir = cfg.music_dir
    if music_dir.exists():
        for ext in ("*.mp3", "*.wav", "*.m4a", "*.ogg"):
            hits = sorted(music_dir.glob(ext))
            if hits:
                print(f"  música: archivo local {hits[0].name}")
                return hits[0]

    if cfg.mureka_api_key:
        try:
            from youtube_pipeline.generators.mureka_music import generate_music_mureka
            prompt = (
                "calm cinematic background music for a youtube video"
                + (f" about {topic}" if topic else "")
                + ", soft piano and warm pads, steady subtle groove, non-distracting, loopable"
            )
            print("  música: generando con Mureka.ai ...")
            track = generate_music_mureka(job_dir / "mureka_music.mp3", prompt=prompt)
            if track:
                print("  música: Mureka.ai OK")
                return track
        except Exception as e:
            print(f"  [música] Mureka falló ({str(e)[:80]}), uso cama sintetizada")

    try:
        bed = job_dir / "music_bed.wav"
        generate_music_bed(bed, duration=40.0)
        print("  música: cama ambiental sintetizada (fallback)")
        return bed
    except Exception as e:
        print(f"  [música] no disponible: {str(e)[:60]}")
        return None


def crear_video(
    topic: str,
    canal: str = "MZSHARD",
    idioma: str = "es",
    niche: str = "inteligencia artificial y tecnología",
    output_dir: Path | None = None,
    plan: dict | None = None,
) -> Path:
    """
    Genera el video completo para `topic` y devuelve la ruta del MP4 final.

    Si `plan` se proporciona (dict ya escrito), se usa tal cual y NO se llama a
    la API de Claude. Útil cuando no hay crédito de API: el guion se aporta a
    mano o desde un archivo JSON (--plan-file).
    """
    if plan is None:
        if not cfg.anthropic_api_key:
            raise SystemExit("Falta ANTHROPIC_API_KEY (para generar el guion con Claude).")
        print(f"\n[1/3] Generando guion con Claude sobre: {topic!r} ...")
        plan = generate_video_plan(topic, niche=niche, language=idioma, channel=canal)
    else:
        print(f"\n[1/3] Usando plan provisto (sin llamar a la API) ...")
    print(f"  Título: {plan.get('title')}")
    print(f"  Items : {len(plan.get('items', []))}")

    job_dir = (output_dir or cfg.output_dir) / _slug(topic)
    job_dir.mkdir(parents=True, exist_ok=True)
    music = _resolve_music(job_dir, topic=topic)

    # ── Entrega 1: video completo (16:9) ────────────────────────────────────
    segments, meta = _plan_to_segments(plan, topic, canal)
    print(f"\n[2/3] Renderizando VIDEO COMPLETO ({len(segments)} segmentos) ...")
    full = render_video(segments, meta, job_dir / "completo", channel=canal,
                        is_shorts=False, music_path=music)

    # ── Entrega 2: Short / Reel / TikTok (9:16) ─────────────────────────────
    short_built = _short_segments(plan, topic)
    short = None
    if short_built:
        s_segments, s_meta = short_built
        print(f"\n[3/3] Renderizando SHORT vertical ({len(s_segments)} segmentos) ...")
        short = render_video(s_segments, s_meta, job_dir / "short", channel=canal,
                             is_shorts=True, music_path=music)
    else:
        print("\n[3/3] El plan no trae sección 'short' — omitido.")

    print("\n== ENTREGAS ==")
    print(f"  Completo: {full}")
    print(f"  Short   : {short or '(no generado)'}")
    return full, short


def main():
    ap = argparse.ArgumentParser(description="Crea un video completo a partir de un tema.")
    ap.add_argument("tema", help="Tema del video, p. ej. 'Los 7 riesgos de usar IA en 2026'")
    ap.add_argument("--canal", default="MZSHARD", help="Nombre del canal (branding)")
    ap.add_argument("--idioma", default="es", help="Idioma de la narración (es, en, ...)")
    ap.add_argument("--niche", default="inteligencia artificial y tecnología", help="Nicho del canal")
    ap.add_argument("--plan-file", default=None,
                    help="Ruta a un JSON con el plan ya escrito (omite la API de Claude)")
    args = ap.parse_args()

    plan = None
    if args.plan_file:
        plan = json.loads(Path(args.plan_file).read_text(encoding="utf-8"))

    full, short = crear_video(args.tema, canal=args.canal, idioma=args.idioma,
                              niche=args.niche, plan=plan)
    print(f"\n== LISTO ==\n  Completo: {full}\n  Short: {short or '(no generado)'}")


if __name__ == "__main__":
    main()
