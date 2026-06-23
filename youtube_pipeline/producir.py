# -*- coding: utf-8 -*-
"""
PIPELINE UNIFICADO MZSHARD — un comando por video (o por lote).

Tú das un nombre/tema (y opcionalmente detalles + en qué voz) y genera:
  guion (Claude o archivo .json) -> narración (tu voz F5 o ElevenLabs)
  -> imágenes verticales/horizontales (Pexels) -> animación Remotion
  -> entrega COMPLETO (16:9) + SHORT (9:16) en entregas/.

Corre dentro del entorno .venv-voz (que ya trae torch + F5 + requests).
Las APIs (Claude, ElevenLabs, Pexels) se llaman por HTTP con requests, así que
NO hace falta instalar SDKs ni el stack viejo de ffmpeg/PIL.

USO RÁPIDO (ver también: produce.ps1 en la raíz):
  # Un video, con tu voz clonada:
  python -m youtube_pipeline.producir "Los 5 errores que arruinan un Data Lake" --voz f5

  # Con detalles y en ElevenLabs (recomendado para términos técnicos en inglés):
  python -m youtube_pipeline.producir "BigQuery vs Snowflake" --voz elevenlabs ^
      --detalles "enfoque en costos y performance, tono directo"

  # Desde un guion ya escrito (sin gastar API de Claude):
  python -m youtube_pipeline.producir "Entrevista Data Architect" ^
      --plan-file youtube_pipeline/examples/plans/p11_entrevista_data_architect.json --voz f5

  # LOTE: varias ideas, una por línea (admite "tema | detalles"):
  python -m youtube_pipeline.producir --lote mis_ideas.txt --voz elevenlabs
"""

import os
import re
import sys
import glob
import json
import time
import shutil
import argparse
import subprocess
import urllib.request
import urllib.parse
from pathlib import Path

# ── Rutas del proyecto ───────────────────────────────────────────────────────
REPO = Path(__file__).resolve().parents[1]
PKG = REPO / "youtube_pipeline"
REMOTION = REPO / "remotion"
PUBLIC = REMOTION / "public"
MANIFESTS = REMOTION / "manifests"
MEDIA = REPO / "media"
OUTPUT = PKG / "output"
ENTREGAS = REPO / "entregas"
VENV = REPO / ".venv-voz"

FPS = 30
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

PALETTES = [
    [255, 107, 53], [233, 69, 96], [83, 168, 182], [199, 44, 65],
    [102, 252, 241], [157, 78, 221], [255, 211, 105], [252, 163, 17],
]
CODE_RE = re.compile(
    r"[()*=]|SELECT|FROM|GROUP|JOIN|CASE|OVER|QUALIFY|COUNT|SUM|AVG|"
    r"DATE_TRUNC|ROW_NUMBER|PARTITION|WHERE|RANK|UNION", re.I)


# ── Claves (.env) ────────────────────────────────────────────────────────────
def load_env() -> dict:
    env = {}
    f = PKG / ".env"
    if f.exists():
        for raw in f.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    # variables de entorno tienen prioridad
    for k in ("ANTHROPIC_API_KEY", "PEXELS_API_KEY", "ELEVENLABS_API_KEY",
              "ELEVENLABS_VOICE_ID", "CLAUDE_MODEL"):
        if os.environ.get(k):
            env[k] = os.environ[k]
    return env


ENV = load_env()
CLAUDE_MODEL = ENV.get("CLAUDE_MODEL", "claude-sonnet-4-6")


# ── Generación del plan con Claude (HTTP, con reintentos por DNS) ─────────────
PLAN_SYSTEM = ("Eres un guionista experto de YouTube para el canal MZSHARD "
               "(nicho: IA, datos y tecnología). Creas videos con un hook potente, "
               "narración fluida y valor real. Devuelves SIEMPRE JSON válido y nada más.")


def _plan_prompt(topic: str, detalles: str, canal: str) -> str:
    extra = f"\nDetalles/indicaciones del autor: {detalles}\n" if detalles else ""
    return f"""Crea el plan de un video de YouTube para el canal {canal} sobre: "{topic}"

Nicho: inteligencia artificial, datos y tecnología. Idioma: español (España/LatAm neutro).{extra}
Reglas:
- Si el tema menciona una cantidad ("7 errores", "5 herramientas"), produce EXACTAMENTE esa cantidad de items. Si no, elige entre 5 y 7 items.
- Narración natural, con gancho, que fluya entre puntos. Tono educativo y entretenido, profesional.
- "broll": términos de búsqueda de fotos de stock EN INGLÉS, concretos y visuales (sin marcas/logos). 3 por item.
- "title" máx 60 caracteres. "title" de cada item: 1-4 palabras (van GRANDES en pantalla). "tagline": una línea (~50 chars).

Responde ÚNICAMENTE con este JSON (sin markdown):
{{
  "title": "Título del video (máx 60 chars)",
  "description": "Descripción para YouTube con keywords (150-300 chars)",
  "tags": ["tag1","tag2","..."],
  "thumbnail_text": "Texto miniatura (máx 4 palabras)",
  "intro_card": "Título corto tarjeta de intro (2-4 palabras)",
  "intro_text": "Narración del hook/intro: 4-6 frases que enganchen y presenten el tema",
  "intro_broll": ["english query 1","english query 2","english query 3"],
  "items": [
    {{"title":"Punto (1-4 palabras)","tagline":"Subtítulo corto","text":"Narración 4-7 frases con valor real","broll":["en query","en query","en query"]}}
  ],
  "outro_text": "Cierre pidiendo suscribirse y anticipando el próximo video",
  "short": {{
    "hook_card": "Título Short (2-3 palabras)",
    "hook_text": "Gancho 1-2 frases muy potente",
    "hook_broll": ["en query","en query"],
    "points": [
      {{"title":"Clave (1-3 palabras)","tagline":"una línea","text":"1-2 frases que adelanten el valor SIN contarlo todo","broll":["en query","en query"]}}
    ],
    "cta_text": "Cierre que INVITA a ver el video completo (1-2 frases)"
  }}
}}

Para "short": 2-3 points (los más llamativos), ~40 s total, generar curiosidad sin resolver todo."""


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_plan(topic: str, detalles: str, canal: str) -> dict:
    key = ENV.get("ANTHROPIC_API_KEY", "")
    if not key:
        raise SystemExit("Falta ANTHROPIC_API_KEY en youtube_pipeline/.env (para generar el guion).")
    body = json.dumps({
        "model": CLAUDE_MODEL, "max_tokens": 8192, "system": PLAN_SYSTEM,
        "messages": [{"role": "user", "content": _plan_prompt(topic, detalles, canal)}],
    }).encode("utf-8")
    last = ""
    for i in range(1, 16):
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages", data=body,
                headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                         "content-type": "application/json", "User-Agent": UA})
            resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
            return _parse_json(resp["content"][0]["text"])
        except Exception as e:
            last = str(e)[:120]
            print(f"  [claude] reintento {i}/15: {last}", flush=True)
            time.sleep(5)
    raise SystemExit(f"No se pudo generar el plan con Claude: {last}")


# ── Voz: ElevenLabs (HTTP) ───────────────────────────────────────────────────
def el_tts(text: str, out_mp3: Path, voice_id: str) -> Path:
    key = ENV.get("ELEVENLABS_API_KEY", "")
    if not key:
        raise SystemExit("Falta ELEVENLABS_API_KEY en youtube_pipeline/.env (--voz elevenlabs).")
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({
        "text": text, "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
    }).encode("utf-8")
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    last = ""
    for i in range(1, 11):
        try:
            req = urllib.request.Request(url, data=body, headers={
                "xi-api-key": key, "content-type": "application/json",
                "accept": "audio/mpeg", "User-Agent": UA})
            data = urllib.request.urlopen(req, timeout=120).read()
            out_mp3.write_bytes(data)
            return out_mp3
        except Exception as e:
            last = str(e)[:120]
            print(f"  [elevenlabs] reintento {i}/10: {last}", flush=True)
            time.sleep(4)
    raise SystemExit(f"ElevenLabs falló: {last}")


# ── Voz: F5 (tu voz clonada, en proceso con torch) ───────────────────────────
_F5 = None


def _f5_model():
    global _F5
    if _F5 is not None:
        return _F5
    for b in glob.glob(str(VENV / "ffmpeg7-shared" / "*" / "bin")):
        try:
            os.add_dll_directory(b)
        except Exception:
            pass
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    import torch  # noqa: F401  (inicializa DLLs antes que f5_tts)
    from f5_tts.api import F5TTS
    ckpt = VENV / "f5-spanish" / "model_1200000.safetensors"
    vocab = VENV / "f5-spanish" / "vocab.txt"
    print("  [f5] cargando modelo...", flush=True)
    _F5 = F5TTS(model="F5TTS_Base", ckpt_file=str(ckpt), vocab_file=str(vocab), device="cuda")
    print("  [f5] listo.", flush=True)
    return _F5


def f5_tts(text: str, out_wav: Path, speed: float = 1.0) -> Path:
    m = _f5_model()
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    ref = PKG / "assets" / "voces" / "mi_voz_intro.wav"
    ref_text = ("Hola, ¿qué tal? Bienvenido una vez más a mi canal. Soy yo, y hoy te "
                "traigo algo que de verdad va a cambiar tu forma de ver la inteligencia artificial.")
    kw = dict(ref_file=str(ref), ref_text=ref_text, gen_text=text,
              file_wave=str(out_wav), remove_silence=True)
    try:
        m.infer(speed=speed, **kw)            # si F5 soporta 'speed' (recomendado < 1.0)
    except TypeError:
        m.infer(**kw)
    return out_wav


# ── Pexels (imágenes) ────────────────────────────────────────────────────────
def collect_photos(queries, n, out_dir, prefix, orientation):
    key = ENV.get("PEXELS_API_KEY", "")
    out_dir.mkdir(parents=True, exist_ok=True)
    got, qi, seen, attempts = 0, 0, set(), 0
    while got < n and attempts < n * 4 + 10:
        attempts += 1
        q = queries[qi % len(queries)]
        qi += 1
        url = (f"https://api.pexels.com/v1/search?query={urllib.parse.quote(q)}"
               f"&orientation={orientation}&per_page=10&size=large")
        try:
            req = urllib.request.Request(url, headers={
                "Authorization": key, "User-Agent": UA, "Accept": "application/json"})
            data = json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print(f"      [pexels] reintento '{q}': {str(e)[:50]}", flush=True)
            time.sleep(3)
            continue
        for photo in data.get("photos", []):
            pid = photo.get("id")
            if pid in seen:
                continue
            seen.add(pid)
            src = photo["src"].get("large2x") or photo["src"].get("large") or photo["src"].get("original")
            try:
                r2 = urllib.request.Request(src, headers={"User-Agent": UA})
                (out_dir / f"{prefix}_{got}.jpg").write_bytes(urllib.request.urlopen(r2, timeout=60).read())
                got += 1
            except Exception as e:
                print(f"      [pexels] descarga fallo: {str(e)[:50]}", flush=True)
            if got >= n:
                break
    return got


# ── Plan -> segmentos (mismo contrato que la infra Remotion) ──────────────────
def _slug(text, n=40):
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in text[:n]).strip("_") or "video"


def plan_to_segments(plan, topic, canal):
    intro_card = plan.get("intro_card") or plan.get("thumbnail_text") or topic
    welcome = (f"¡Bienvenido a {canal}! Tu canal de inteligencia artificial y tecnología. "
               f"Hoy hablamos de {topic.lower()}. Quédate hasta el final. Vamos con ello.")
    segs = [{"text": welcome, "kind": "welcome", "label": canal,
             "tagline": "Inteligencia Artificial y Tecnología", "number": "", "broll": []}]
    segs.append({"text": plan.get("intro_text", ""), "kind": "topic", "label": intro_card,
                 "number": "", "tagline": plan.get("title", ""), "broll": plan.get("intro_broll") or []})
    for i, item in enumerate(plan.get("items", []), start=1):
        segs.append({"text": item.get("text", ""), "kind": "item", "label": item.get("title", f"Punto {i}"),
                     "number": item.get("number") or f"{i:02d}", "tagline": item.get("tagline", ""),
                     "broll": item.get("broll") or []})
    segs.append({"text": plan.get("outro_text", "Suscríbete al canal para no perderte el próximo video."),
                 "kind": "outro", "label": "SUSCRÍBETE", "number": "", "tagline": "", "broll": []})
    return segs


def short_segments(plan, topic):
    short = plan.get("short")
    if not short:
        return None
    segs = [{"text": short.get("hook_text", ""), "kind": "topic",
             "label": short.get("hook_card") or plan.get("thumbnail_text", topic),
             "number": "", "tagline": "", "broll": short.get("hook_broll") or []}]
    for i, pt in enumerate(short.get("points", []), start=1):
        segs.append({"text": pt.get("text", ""), "kind": "item", "label": pt.get("title", f"Tip {i}"),
                     "number": f"{i:02d}", "tagline": pt.get("tagline", ""), "broll": pt.get("broll") or []})
    segs.append({"text": short.get("cta_text", "Mira el video completo en el canal. Te espero."),
                 "kind": "outro", "label": "VE EL VIDEO", "number": "", "tagline": "", "broll": []})
    return segs


# ── Helpers de audio/render ──────────────────────────────────────────────────
def _audio_dur(path):
    r = subprocess.run(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 6.0


def _seg_audio(audio_dir, i):
    """Devuelve el audio del segmento i sea .wav (F5) o .mp3 (ElevenLabs)."""
    for ext in (".wav", ".mp3"):
        p = audio_dir / f"seg_{i:03d}{ext}"
        if p.exists() and p.stat().st_size > 1024:
            return p
    return None


def prepare(segments, job_dir, is_short, voice, speed):
    (job_dir / "audio").mkdir(parents=True, exist_ok=True)
    (job_dir / "img").mkdir(parents=True, exist_ok=True)
    orient = "portrait" if is_short else "landscape"
    max_shots = 3 if is_short else 5
    vid = ENV.get("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
    for i, seg in enumerate(segments):
        text = (seg.get("text") or "").strip()
        audio = _seg_audio(job_dir / "audio", i)
        if audio is None:                                  # reanudable: si ya existe, no regenera
            if voice == "f5":
                audio = f5_tts(text, job_dir / "audio" / f"seg_{i:03d}.wav", speed=speed)
            else:
                audio = el_tts(text, job_dir / "audio" / f"seg_{i:03d}.mp3", vid)
        dur = _audio_dur(audio)
        print(f"    [{i+1}/{len(segments)}] {seg.get('kind')} voz {dur:.0f}s", flush=True)
        if seg.get("kind") in ("topic", "item") and seg.get("broll"):
            if (job_dir / "img" / f"ph_{i:03d}_0.jpg").exists():
                continue
            n = max(2, min(max_shots, round(dur / 4.0)))
            collect_photos(seg["broll"], n, job_dir / "img", f"ph_{i:03d}", orient)


def export(segments, fmt, slug, canal, music_name):
    job = OUTPUT / slug / ("short" if fmt == "short" else "completo")
    audio_dir, img_dir = job / "audio", job / "img"
    asset = f"{slug[:24]}_{fmt}"
    dest = PUBLIC / asset
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    man_segs = []
    for i, seg in enumerate(segments):
        a = _seg_audio(audio_dir, i)
        audio_rel = None
        if a:
            shutil.copy2(a, dest / a.name)
            audio_rel = f"{asset}/{a.name}"
        frames = max(1, round(_audio_dur(a) * FPS)) if a else 6 * FPS
        img_rels = []
        for ph in sorted(img_dir.glob(f"ph_{i:03d}_*.jpg")):
            shutil.copy2(ph, dest / ph.name)
            img_rels.append(f"{asset}/{ph.name}")
        tagline = seg.get("tagline", "") or ""
        man_segs.append({
            "kind": seg.get("kind", "item"), "title": seg.get("label", ""),
            "number": seg.get("number", "") or "", "tagline": tagline,
            "code": bool(tagline and CODE_RE.search(tagline)),
            "text": seg.get("text", "") or "", "audio": audio_rel,
            "durationInFrames": frames, "images": img_rels,
            "accent": PALETTES[i % len(PALETTES)],
        })

    # música de media/music (por nombre o rotación estable)
    music_rel = None
    mdir = MEDIA / "music"
    tracks = sorted(p for p in mdir.glob("*") if p.suffix.lower() in (".mp3", ".wav", ".m4a", ".ogg")) if mdir.exists() else []
    track = next((t for t in tracks if music_name and t.stem.lower() == music_name.lower()), None)
    if track is None and tracks:
        track = tracks[sum(ord(c) for c in (slug + fmt)) % len(tracks)]
    if track:
        shutil.copy2(track, dest / track.name)
        music_rel = f"{asset}/{track.name}"
        print(f"  música: {track.name}", flush=True)

    # logo desde media/logo
    logo_rel = None
    ldir = MEDIA / "logo"
    logos = [p for p in sorted(ldir.glob("*")) if p.suffix.lower() in (".png", ".webp", ".jpg", ".jpeg")] if ldir.exists() else []
    if logos:
        shutil.copy2(logos[0], dest / logos[0].name)
        logo_rel = f"{asset}/{logos[0].name}"

    manifest = {"fps": FPS, "channel": canal, "music": music_rel, "logo": logo_rel, "segments": man_segs}
    MANIFESTS.mkdir(parents=True, exist_ok=True)
    mpath = MANIFESTS / f"{asset}.json"
    mpath.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    comp = "Short" if fmt == "short" else "Video"
    total = sum(s["durationInFrames"] for s in man_segs)
    print(f"  manifest {mpath.name}  comp={comp}  ~{total/FPS:.0f}s", flush=True)
    return comp, mpath


def render(comp, manifest, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["npx", "remotion", "render", "src/index.ts", comp, str(out),
           f"--props={manifest}", "--concurrency=4", "--log=error"]
    print(f"  [remotion] {comp} -> {out.name}", flush=True)
    r = subprocess.run(cmd, cwd=str(REMOTION), shell=(os.name == "nt"))
    if r.returncode != 0 or not out.exists():
        raise RuntimeError(f"Remotion falló para {comp}")


def compress(src, dst, crf=26):
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(src), "-c:v", "libx264", "-preset", "medium",
                    "-crf", str(crf), "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(dst)],
                   check=True, capture_output=True)


# ── Orquestación de un video ─────────────────────────────────────────────────
def produce_one(topic, detalles, voice, canal, do_short, plan_file, music_name, speed):
    print(f"\n{'='*64}\n  {topic}\n  voz={voice}  canal={canal}\n{'='*64}", flush=True)
    if plan_file:
        plan = json.loads(Path(plan_file).read_text(encoding="utf-8"))
        print(f"  plan: archivo {Path(plan_file).name}", flush=True)
    else:
        print("  plan: generando con Claude...", flush=True)
        plan = generate_plan(topic, detalles, canal)
    print(f"  título: {plan.get('title')}  items: {len(plan.get('items', []))}", flush=True)

    slug = _slug(topic)
    base = _slug(plan.get("title", topic))

    full = plan_to_segments(plan, topic, canal)
    print(f"\n[completo] voz+imágenes ({len(full)} seg)...", flush=True)
    prepare(full, OUTPUT / slug / "completo", is_short=False, voice=voice, speed=speed)
    comp_f, man_f = export(full, "full", slug, canal, music_name)
    tmp_f = OUTPUT / slug / "_full_raw.mp4"
    render(comp_f, man_f, tmp_f)
    out_f = ENTREGAS / f"{base}_COMPLETO_ANIMADO.mp4"
    compress(tmp_f, out_f)
    print(f"  ✓ {out_f.name} ({out_f.stat().st_size//1048576} MB)", flush=True)

    out_s = None
    short = short_segments(plan, topic) if do_short else None
    if short:
        print(f"\n[short] voz+imágenes ({len(short)} seg)...", flush=True)
        prepare(short, OUTPUT / slug / "short", is_short=True, voice=voice, speed=speed)
        comp_s, man_s = export(short, "short", slug, canal, music_name)
        tmp_s = OUTPUT / slug / "_short_raw.mp4"
        render(comp_s, man_s, tmp_s)
        out_s = ENTREGAS / f"{base}_SHORT_ANIMADO.mp4"
        compress(tmp_s, out_s)
        print(f"  ✓ {out_s.name} ({out_s.stat().st_size//1048576} MB)", flush=True)

    return out_f, out_s


def main():
    ap = argparse.ArgumentParser(description="Pipeline unificado MZSHARD (voz F5/ElevenLabs + Remotion).")
    ap.add_argument("tema", nargs="?", help="Nombre/tema del video")
    ap.add_argument("--voz", choices=["f5", "elevenlabs"], default="elevenlabs",
                    help="Voz de la narración (default: elevenlabs)")
    ap.add_argument("--detalles", default="", help="Indicaciones extra para el guion")
    ap.add_argument("--plan-file", default=None, help="Usar un plan .json ya escrito (no llama a Claude)")
    ap.add_argument("--canal", default="MZSHARD")
    ap.add_argument("--musica", default=None, help="Nombre de pista en media/music (sin extensión)")
    ap.add_argument("--velocidad", type=float, default=1.0, help="Velocidad de la voz F5 (1.0 normal, <1 más lenta)")
    ap.add_argument("--no-short", action="store_true", help="No generar el Short")
    ap.add_argument("--lote", default=None, help="Archivo con una idea por línea ('tema | detalles')")
    args = ap.parse_args()

    trabajos = []
    if args.lote:
        for raw in Path(args.lote).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            tema, _, det = line.partition("|")
            trabajos.append((tema.strip(), det.strip()))
    elif args.tema:
        trabajos.append((args.tema, args.detalles))
    else:
        ap.error("Da un tema, o usa --lote archivo.txt")

    print(f"== {len(trabajos)} video(s) a producir | voz={args.voz} ==", flush=True)
    hechos = []
    for tema, det in trabajos:
        try:
            f, s = produce_one(tema, det or args.detalles, args.voz, args.canal,
                               not args.no_short, args.plan_file, args.musica, args.velocidad)
            hechos.append((tema, f, s))
        except Exception as e:
            print(f"  ✗ ERROR en '{tema}': {str(e)[:160]}", flush=True)

    print(f"\n{'='*64}\n  ENTREGAS ({len(hechos)})", flush=True)
    for tema, f, s in hechos:
        print(f"  • {tema}\n      completo: {f}\n      short:    {s or '(omitido)'}", flush=True)


if __name__ == "__main__":
    main()
