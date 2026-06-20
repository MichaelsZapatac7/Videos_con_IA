# Configuración del MCP de Edición de Video

Este MCP le da a Claude acceso directo para editar videos en tu máquina local.
Una vez configurado, puedes pedirme que recorte, una, subtitule y exporte videos
sin salir de la conversación.

---

## 1. Instalar FFmpeg (requisito)

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
Descarga desde https://ffmpeg.org/download.html y agrega al PATH.

**Linux/Ubuntu:**
```bash
sudo apt update && sudo apt install ffmpeg
```

Verifica: `ffmpeg -version`

---

## 2. Instalar el MCP de video (video-audio-mcp)

```bash
# Clonar el servidor MCP
git clone https://github.com/misbahsy/video-audio-mcp.git ~/video-audio-mcp
cd ~/video-audio-mcp

# Instalar dependencias (necesitas uv: pip install uv)
uv sync
```

---

## 3. Configurar Claude Desktop

Abre el archivo de configuración de Claude Desktop:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Agrega (o fusiona) este bloque en `mcpServers`:

```json
{
  "mcpServers": {
    "video-editor": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/TU_USUARIO/video-audio-mcp",
        "run",
        "server.py"
      ]
    }
  }
}
```

> Reemplaza `/Users/TU_USUARIO/video-audio-mcp` con la ruta real donde clonaste el repo.

**Reinicia Claude Desktop** después de guardar.

---

## 4. Verificar que funciona

En una nueva conversación con Claude, escribe:
> "Lista las herramientas de video que tienes disponibles"

Deberías ver herramientas como `trim_video`, `add_subtitles`, `concatenate_videos`, etc.

---

## 5. Qué puedo hacer con el MCP activo

Una vez configurado, puedes decirme cosas como:

- *"Toma el video raw.mp4, recórtalo a los primeros 3 minutos y agrega el audio de voiceover.mp3"*
- *"Une todos los clips en la carpeta /output y agrega fundidos entre ellos"*
- *"Agrega subtítulos automáticos al video final.mp4 en español"*
- *"Convierte el video a formato vertical 9:16 para Shorts"*
- *"Agrega el logo watermark en la esquina superior derecha"*
- *"Cambia el bitrate y exporta para YouTube optimizado"*

---

## 6. Pipeline completo local

```bash
# 1. Clonar el repositorio
git clone https://github.com/michaelszapatac7/ia.git
cd ia

# 2. Configurar variables de entorno
cp youtube_pipeline/.env.example youtube_pipeline/.env
# Editar .env con tus API keys

# 3. Instalar dependencias Python
pip install -r youtube_pipeline/requirements.txt

# 4. Generar tu primer video
python -m youtube_pipeline.main \
  --topic "Los 5 modelos de IA más importantes de 2026" \
  --niche "tecnología e inteligencia artificial" \
  --lang es \
  --duration 480

# 5. Generar un YouTube Short
python -m youtube_pipeline.main \
  --topic "Este truco de IA nadie te está contando" \
  --shorts

# 6. Video largo + 3 Shorts automáticos
python -m youtube_pipeline.main \
  --topic "Cómo automatizo mi negocio con IA" \
  --also-shorts
```

---

## Herramientas alternativas recomendadas

| Herramienta | Uso | Precio |
|------------|-----|--------|
| [reap.video](https://reap.video) | Clips virales desde YouTube + captions automáticos | $9.99/mes |
| [Shotstack](https://shotstack.io) | API de renderizado cloud para templates | $0.20/min renderizado |
| [Higgsfield](https://higgsfield.ai) | Generar clips de video con IA | $15/mes starter |
| [ElevenLabs](https://elevenlabs.io) | Voiceovers naturales | $5/mes starter |
| [Pexels API](https://pexels.com/api) | Stock footage HD gratis | Gratis |
| OpenAI Whisper | Subtítulos automáticos locales | Gratis (local) |
