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

# 3. Generar video
python -m youtube_pipeline.main --topic "Los 5 modelos de IA de 2026"
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
