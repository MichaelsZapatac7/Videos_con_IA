# ⏳ Pendientes de la voz F5 (mejorar antes de producción seria)

Feedback del 2026-06-23 sobre la narración F5 en el video de la entrevista.
**No bloquea el pipeline** (ElevenLabs queda como voz de calidad mientras tanto),
pero hay que pulir F5 para usarla en serio:

## 1. Muletilla "artificial" al inicio de frases
Antes de empezar algunas oraciones se cuela un "artificial" que suena fatal.
- Causa probable: artefacto de F5 al concatenar batches / la referencia o el
  `ref_text` "inteligencia artificial" filtrándose. Revisar `remove_silence`,
  el split por frases y probar otra muestra/ref_text sin "artificial".

## 2. Va demasiado rápido → el inglés no se entiende
En tecnología casi todo es inglés (WHERE, RANK, QUALIFY, Shuffle, Broadcast...).
A esa velocidad esas palabras no se entienden, y eso es crítico para el canal.
- Acciones a probar:
  - Bajar la velocidad de F5 (parámetro `speed` < 1.0 en `infer`, o `nfe_step` /
    `cross_fade_duration`), o post-procesar con atempo en ffmpeg.
  - Insertar micro-pausas alrededor de términos en inglés en el guion.
  - Evaluar pronunciación: quizá escribir términos clave fonéticamente, o dejar
    los términos en inglés con marcas de énfasis.

## 3. Idea de fondo
Comparar F5 vs ElevenLabs en una frase con muchos términos en inglés y decidir
si F5 necesita afinado de velocidad/claridad antes de reemplazar a ElevenLabs.

> Mientras tanto: el pipeline soporta ambas voces (`--voz elevenlabs` | `--voz f5`).
> Para contenido técnico serio, usar `elevenlabs` hasta resolver 1 y 2.
