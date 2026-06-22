"""
Script generator using Claude API.
Produces structured video scripts with hooks, segments, and CTAs.
"""

import json
from dataclasses import dataclass
from typing import Optional
import anthropic

from ..config import cfg


@dataclass
class VideoScript:
    title: str
    description: str
    tags: list[str]
    hook: str                    # First 3-5 seconds — must grab attention
    segments: list[dict]         # [{text, visual_cue, duration_seconds}]
    call_to_action: str
    thumbnail_text: str
    total_estimated_seconds: int
    is_shorts: bool = False


SYSTEM_PROMPT = """Eres un experto creador de contenido para YouTube con miles de suscriptores.
Generas guiones virales, atractivos y con valor real para el espectador.
Siempre incluyes un hook impactante en los primeros 5 segundos.
Escribes en el idioma que se te pide y adaptas el tono al nicho.
Respondes SOLO con JSON válido, sin texto adicional."""


def generate_script(
    topic: str,
    niche: str = "tecnología e IA",
    language: str = "es",
    target_duration: int = 600,  # seconds (10 min)
    is_shorts: bool = False,
    style: str = "educativo-entretenido",
    extra_context: str = "",
) -> VideoScript:
    """
    Generate a full video script for the given topic.

    Args:
        topic: Main video topic
        niche: Channel niche/category
        language: Language code ('es', 'en', etc.)
        target_duration: Target video length in seconds
        is_shorts: If True, generates a 60-second Shorts script
        style: Video style ('educativo', 'motivacional', 'tutorial', 'lista', etc.)
        extra_context: Additional context or instructions
    """
    if is_shorts:
        target_duration = 55
        format_desc = "YouTube Short de máximo 60 segundos"
    else:
        format_desc = f"video de YouTube de aproximadamente {target_duration // 60} minutos"

    prompt = f"""Genera el guión completo para un {format_desc} sobre: "{topic}"

Nicho del canal: {niche}
Idioma: {language}
Estilo: {style}
{f'Contexto adicional: {extra_context}' if extra_context else ''}

Responde ÚNICAMENTE con este JSON (sin markdown, sin texto extra):
{{
  "title": "Título optimizado para SEO y clicks (máx 60 chars)",
  "description": "Descripción para YouTube con keywords (150-300 chars)",
  "tags": ["tag1", "tag2", ...],  // 10-15 tags relevantes
  "hook": "Texto del hook — las primeras 3-5 frases que aparecerán primero",
  "segments": [
    {{
      "text": "Texto que narra el locutor en este segmento",
      "visual_cue": "Descripción de qué mostrar visualmente (para buscar stock footage o generar IA)",
      "duration_seconds": 30
    }}
  ],
  "call_to_action": "Texto del CTA al final del video",
  "thumbnail_text": "Texto corto y llamativo para la miniatura (máx 5 palabras)",
  "total_estimated_seconds": {target_duration},
  "is_shorts": {str(is_shorts).lower()}
}}

IMPORTANTE:
- El hook debe crear curiosidad o prometer valor INMEDIATO
- Cada segmento debe fluir naturalmente al siguiente
- Los visual_cue deben ser específicos y descriptivos (p.ej: "persona trabajando en laptop de noche, luz azul")
- El CTA debe pedir suscribirse y ver el próximo video relacionado
"""

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    message = client.messages.create(
        model=cfg.claude_model,
        max_tokens=4096,
        messages=[
            {"role": "user", "content": prompt}
        ],
        system=SYSTEM_PROMPT,
    )

    raw = message.content[0].text.strip()
    # Strip any accidental markdown code fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)

    return VideoScript(
        title=data["title"],
        description=data["description"],
        tags=data["tags"],
        hook=data["hook"],
        segments=data["segments"],
        call_to_action=data["call_to_action"],
        thumbnail_text=data["thumbnail_text"],
        total_estimated_seconds=data["total_estimated_seconds"],
        is_shorts=data.get("is_shorts", is_shorts),
    )


PLAN_SYSTEM_PROMPT = """Eres un guionista experto de YouTube para el canal MZSHARD (nicho: IA y tecnología).
Creas videos tipo ranking/lista con un hook potente, narración fluida y valor real.
Devuelves SIEMPRE JSON válido y nada más."""


def _parse_json(raw: str) -> dict:
    """Limpia fences de markdown y parsea JSON."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def generate_video_plan(
    topic: str,
    niche: str = "inteligencia artificial y tecnología",
    language: str = "es",
    channel: str = "MZSHARD",
) -> dict:
    """
    Genera el PLAN completo de un video enriquecido a partir de un tema.

    A diferencia de generate_script, este produce todo lo que necesita el
    builder con B-roll: por cada punto da un título de tarjeta, un tagline,
    la narración y 3 búsquedas de B-roll EN INGLÉS (Pexels funciona mejor así).

    Devuelve un dict con: title, description, tags, thumbnail_text,
    intro_text, intro_card, intro_broll, items[], outro_text.
    """
    prompt = f"""Crea el plan de un video de YouTube para el canal {channel} sobre: "{topic}"

Nicho: {niche}. Idioma de la narración y textos en pantalla: {language}.

Reglas:
- Si el tema menciona una cantidad (p. ej. "7 riesgos", "5 herramientas"), produce EXACTAMENTE esa cantidad de items. Si no menciona número, elige entre 5 y 7 items.
- La narración debe ser natural, con gancho y fluir entre puntos. Tono educativo y entretenido.
- Los "broll" son términos de búsqueda de fotos de stock EN INGLÉS, concretos y visuales (NO nombres de marcas ni logos, que no existen en stock). 3 por item.
- "title" máx 60 caracteres, optimizado para clicks.
- "card_title"/"title" de cada item: 1 a 4 palabras (van GRANDES en pantalla).
- "tagline": una sola línea corta (máx ~50 caracteres).

Responde ÚNICAMENTE con este JSON (sin markdown):
{{
  "title": "Título del video (máx 60 chars)",
  "description": "Descripción para YouTube con keywords (150-300 chars)",
  "tags": ["tag1", "tag2", "..."],
  "thumbnail_text": "Texto miniatura (máx 4 palabras)",
  "intro_text": "Narración del hook/intro: 3-4 frases que enganchen y presenten el tema",
  "intro_card": "Título corto para la tarjeta de intro (2-4 palabras)",
  "intro_broll": ["english query 1", "english query 2", "english query 3"],
  "items": [
    {{
      "title": "Título del punto (1-4 palabras)",
      "tagline": "Subtítulo corto de una línea",
      "text": "Narración de este punto (4-7 frases con valor real)",
      "broll": ["english query 1", "english query 2", "english query 3"]
    }}
  ],
  "outro_text": "Narración de cierre pidiendo suscribirse y anticipando el próximo video",
  "short": {{
    "hook_card": "Título corto para la portada del Short (2-3 palabras)",
    "hook_text": "Gancho de 1-2 frases muy potente para los primeros segundos",
    "hook_broll": ["english query 1", "english query 2"],
    "points": [
      {{
        "title": "Punto clave (1-3 palabras)",
        "tagline": "una línea",
        "text": "1-2 frases que adelanten el valor SIN contarlo todo",
        "broll": ["english query 1", "english query 2"]
      }}
    ],
    "cta_text": "Cierre que INVITA a ver el video completo en el canal (1-2 frases)"
  }}
}}

Para "short": elige 2 o 3 "points" (los más llamativos) y que el Short dure ~40 s en total. Debe generar curiosidad y empujar a ver el video largo, NO resolver todo."""

    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)
    message = client.messages.create(
        model=cfg.claude_model,
        max_tokens=8192,
        messages=[{"role": "user", "content": prompt}],
        system=PLAN_SYSTEM_PROMPT,
    )
    return _parse_json(message.content[0].text)


def generate_shorts_from_long(long_script: VideoScript, num_shorts: int = 3) -> list[VideoScript]:
    """Extract viral Short ideas from a long-form video script."""
    client = anthropic.Anthropic(api_key=cfg.anthropic_api_key)

    segments_json = json.dumps(long_script.segments, ensure_ascii=False, indent=2)
    prompt = f"""Tengo este guión de video largo:
Título: {long_script.title}

Segmentos:
{segments_json}

Extrae {num_shorts} ideas para YouTube Shorts virales basadas en los momentos más interesantes.
Cada Short debe durar máximo 55 segundos y tener su propio hook.

Responde ÚNICAMENTE con JSON array:
[
  {{
    "title": "...",
    "description": "...",
    "tags": [...],
    "hook": "...",
    "segments": [...],
    "call_to_action": "...",
    "thumbnail_text": "...",
    "total_estimated_seconds": 55,
    "is_shorts": true
  }}
]"""

    message = client.messages.create(
        model=cfg.claude_model,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    shorts_data = json.loads(raw)
    return [
        VideoScript(
            title=s["title"],
            description=s["description"],
            tags=s["tags"],
            hook=s["hook"],
            segments=s["segments"],
            call_to_action=s["call_to_action"],
            thumbnail_text=s["thumbnail_text"],
            total_estimated_seconds=s["total_estimated_seconds"],
            is_shorts=True,
        )
        for s in shorts_data
    ]
