# Cómo obtener el video FINAL en una sesión nueva (sin perder nada, mínimos tokens)

## ✅ Primero: NO vas a perder nada

| Cosa | ¿Se pierde? | Por qué |
|------|-------------|---------|
| Todo el código (pipeline, gráficos, builders) | **No** | Está commiteado en la rama `claude/youtube-video-editing-twdkix` |
| El diseño de bienvenida MZSHARD + tarjetas | **No** | Es código Python (Pillow), se regenera idéntico |
| La integración de fotos Pexels | **No** | Está en `build_rich.py` — se activa con la key |
| El archivo `.env` con tus keys | **Sí** (por seguridad) | Protegido por gitignore → ponlas como variables de entorno |
| Los modelos de voz Piper | Sí | Se re-descargan solos desde GitHub (el script los baja automáticamente) |

> En resumen: la sesión nueva genera un video **con tu voz ElevenLabs + fotos reales de Pexels + branding MZSHARD** ejecutando un solo comando. No se pierde trabajo.

---

## 🔑 Paso 1 — Guardar las keys como variables de entorno (una sola vez)

Para que las keys sobrevivan a la sesión nueva, ponlas en la configuración del entorno:

1. Clic en el **ícono de nube** (nombre del entorno) → **configuración** (engranaje)
2. Verifica que **Network access** esté en **Full** (o Custom con `*.elevenlabs.io`, `*.pexels.com`)
3. En la sección **Environment variables**, agrega estas 4:

```
ANTHROPIC_API_KEY      = (tu key de Anthropic)
ELEVENLABS_API_KEY     = (tu key de ElevenLabs)
PEXELS_API_KEY         = (tu key de Pexels — gratis en pexels.com/api)
ELEVENLABS_VOICE_ID    = 94zOad0g7T7K4oa7zhDq
```

4. Guarda y abre una **sesión nueva** apuntando al repo `MichaelsZapatac7/IA`
   en la rama `claude/youtube-video-editing-twdkix`.

---

## 🚀 Paso 2 — Pedir el video final (1 frase = mínimos tokens)

En la sesión nueva, escríbeme exactamente:

> **"Corre `bash youtube_pipeline/run_final.sh` y envíame el video"**

Eso ejecuta UN comando que:
1. Instala `ffmpeg` si falta
2. Instala dependencias Python (`elevenlabs`, `Pillow`, `requests`…)
3. Instala `piper-tts` y descarga voces en español desde GitHub (fallback automático)
4. Verifica tus 3 keys (ElevenLabs, Pexels, Anthropic)
5. Genera el video con:
   - **Voz real de ElevenLabs** (tu voice_id)
   - **Fotos HD de Pexels** mezcladas como fondo detrás de cada tarjeta MZSHARD
   - Bienvenida del canal + 7 segmentos IA + outro de suscripción
   - Animación Ken Burns + subtítulos quemados
6. Te lo envío

No necesito re-analizar nada → gasta muy pocos tokens.

---

## 🖼️ Qué hace la integración de fotos Pexels (nuevo)

Para cada segmento del video (`1. FABLE 5`, `2. CLAUDE OPUS 4.8`, etc.) el pipeline:

1. Busca en Pexels una foto relacionada con el `visual_cue` del segmento
   (ej: *"powerful supercomputer"* → foto de servidores HD)
2. La descarga en alta resolución
3. La oscurece (brillo 45%) para que el texto sea legible
4. La mezcla con la tarjeta diseñada: **38% foto + 62% tarjeta MZSHARD**
5. Aplica Ken Burns al resultado

El efecto final: ves la foto real de fondo y encima el diseño del canal.
Si Pexels no está disponible (sin key o sin red), usa solo la tarjeta diseñada → funciona igual.

---

## 💻 Alternativa: ejecutarlo en tu PC/Mac (CERO tokens)

```bash
# 1. Traer el código actualizado
git clone https://github.com/MichaelsZapatac7/IA.git
cd IA
git checkout claude/youtube-video-editing-twdkix

# 2. Poner las keys
cp youtube_pipeline/.env.example youtube_pipeline/.env
#   (edita .env con tus 4 keys)

# 3. Ejecutar el comando único
bash youtube_pipeline/run_final.sh
```

El video aparece en `youtube_pipeline/output/rich_7_ias/`.

---

## 🗂️ Estructura del proyecto

```
youtube_pipeline/
├── config.py                    # Keys y configuración global
├── requirements.txt             # Dependencias Python
├── run_final.sh                 # Script único de producción
├── generators/
│   ├── script_gen.py            # Generación de guión con Claude
│   ├── voiceover.py             # ElevenLabs TTS
│   ├── footage.py               # Pexels videos + fotos (search_pexels_photo)
│   ├── graphics.py              # Tarjetas diseñadas con Pillow (MZSHARD branding)
│   ├── demo_assets.py           # Piper TTS + tarjetas FFmpeg (sin keys)
│   └── download_piper_voices.py # Descarga voces Piper desde GitHub
├── editors/
│   ├── video_editor.py          # FFmpeg: trim, scale, Ken Burns, fade, subtítulos
│   ├── captions.py              # Generación de SRT por frases cortas
│   └── assembler.py             # Pipeline completo de ensamblado
└── examples/
    ├── script_7_ias.py          # Guión "Las 7 IA más poderosas" escrito a mano
    ├── build_rich.py            # Builder principal: foto Pexels + tarjeta + voz EL
    ├── build_full.py            # Builder con Pexels videos + ElevenLabs
    └── build_demo.py            # Builder sin keys (espeak + gradientes)
```
