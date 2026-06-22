# 🎬 YouTube Pipeline — Producción Automática de Videos para @mzcshard

Genera videos completos para YouTube con **un solo comando**: Claude escribe el
guión, ElevenLabs pone la voz, Pexels aporta el footage y FFmpeg edita todo.

## 🚀 Empieza aquí (en orden)

1. **[INSTALACION.md](INSTALACION.md)** — Instalación paso a paso para 🪟 Windows y 🍎 Mac
2. **[GUIA_API_KEYS.md](GUIA_API_KEYS.md)** — Cómo conseguir cada API key (con costos)
3. **[mcp_setup/README.md](mcp_setup/README.md)** — Conectar el MCP para que Claude edite por ti

## ⚡ Resumen ultra rápido

```bash
# 1. Instalar (ver INSTALACION.md para detalles)
pip install -r youtube_pipeline/requirements.txt

# 2. Configurar keys (ver GUIA_API_KEYS.md)
cp youtube_pipeline/.env.example youtube_pipeline/.env   # y edítalo

# 3. Generar video ENRIQUECIDO (B-roll + diseño MZSHARD) a partir de un TEMA
bash youtube_pipeline/crear_video.sh "Los 7 riesgos de usar IA en 2026"
```

## 🎯 Pipeline por TEMA (recomendado)

Tú das un tema y se genera el video completo: guion con Claude, voz ElevenLabs,
**B-roll** de fotos reales por punto, diseño de tarjetas MZSHARD, intro/outro y
subtítulos quemados.

```bash
# Un solo comando — cambia el tema por el que quieras:
bash youtube_pipeline/crear_video.sh "Las 5 mejores apps de IA para estudiar"

# Equivalente en Python:
python -m youtube_pipeline.create_video "Las 5 mejores apps de IA para estudiar"
```

**¿Sin crédito de API de Claude?** Puedes aportar el guion ya escrito en un JSON
(mismo formato que `examples/plan_7_riesgos.json`) y el pipeline lo renderiza sin
llamar a la API:

```bash
python -m youtube_pipeline.create_video "Mi tema" \
  --plan-file youtube_pipeline/examples/plan_7_riesgos.json
```

El resultado queda en `youtube_pipeline/output/<tema>/..._FINAL.mp4`.

### El ejemplo fijo de las 7 IA
```bash
python -m youtube_pipeline.examples.build_rich   # "Las 7 IA más poderosas"
```

## 🔄 Qué hace el pipeline

```
  Tu tema
     │
     ▼
[1] Claude  ──▶ guión (hook + segmentos + CTA + título SEO + tags)
     │
     ▼
[2] ElevenLabs  ──▶ voiceover natural por segmento
     │
     ▼
[3] Pexels  ──▶ footage HD que coincide con cada segmento
     │
     ▼
[4] FFmpeg  ──▶ recorta · une · música · subtítulos · watermark · exporta
     │
     ▼
  Video listo para subir  (.mp4 1080p  ó  Shorts 1080×1920)
```

## 📂 Estructura

```
youtube_pipeline/
├── config.py              # Configuración y API keys
├── main.py                # Punto de entrada (CLI)
├── generators/
│   ├── script_gen.py      # Guiones con Claude
│   ├── voiceover.py       # Voces con ElevenLabs
│   └── footage.py         # Footage de Pexels + Higgsfield
├── editors/
│   ├── video_editor.py    # Operaciones FFmpeg
│   ├── captions.py        # Subtítulos (Whisper o por segmento)
│   └── assembler.py       # Ensamble final
├── mcp_setup/             # Guía del MCP de edición
├── INSTALACION.md         # 👈 Empieza por aquí
└── GUIA_API_KEYS.md       # 👈 Luego por aquí
```

## 💰 Costo para empezar: ~$5-10/mes

Ver desglose completo en [GUIA_API_KEYS.md](GUIA_API_KEYS.md).
