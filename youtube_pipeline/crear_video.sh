#!/usr/bin/env bash
#
# Pipeline de UN SOLO COMANDO por TEMA.
# Tú das un tema y se genera el video completo (guion + voz + B-roll + diseño).
#
#   bash youtube_pipeline/crear_video.sh "Los 7 riesgos de usar IA en 2026"
#
# Requisitos (variables de entorno o youtube_pipeline/.env):
#   ANTHROPIC_API_KEY, ELEVENLABS_API_KEY, PEXELS_API_KEY
#   (opcional) ELEVENLABS_VOICE_ID  -> por defecto usa la voz del canal
#
set -e

if [ -z "$1" ]; then
  echo "Uso: bash youtube_pipeline/crear_video.sh \"Tu tema aquí\""
  echo "Ej.: bash youtube_pipeline/crear_video.sh \"Los 7 riesgos de usar IA en 2026\""
  exit 1
fi
TEMA="$1"

# Ir a la raíz del repo (carpeta padre de este script)
cd "$(dirname "$0")/.."
echo "== Carpeta de trabajo: $(pwd) =="
echo "== Tema: $TEMA =="

# 1) FFmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "== Instalando ffmpeg =="
  (apt-get update -qq && apt-get install -y ffmpeg) \
    || (sudo apt-get update -qq && sudo apt-get install -y ffmpeg)
fi

# 2) Dependencias de Python
echo "== Instalando dependencias de Python =="
pip3 install -q -r youtube_pipeline/requirements.txt

# 3) Piper como fallback de voz (solo si ElevenLabs no está disponible)
if ! command -v piper >/dev/null 2>&1; then
  pip3 install -q piper-tts 2>/dev/null || true
fi
if command -v piper >/dev/null 2>&1; then
  VOICE_DIR="youtube_pipeline/assets/piper_voices"
  if [ ! -f "$VOICE_DIR/es-carlfm-x-low.onnx" ]; then
    python3 -m youtube_pipeline.generators.download_piper_voices || true
  fi
fi

# 4) Verificar claves
python3 - <<'PY'
from youtube_pipeline.config import cfg
import sys
faltan = [k for k,v in {
    "ANTHROPIC_API_KEY": cfg.anthropic_api_key,
    "ELEVENLABS_API_KEY": cfg.elevenlabs_api_key,
    "PEXELS_API_KEY": cfg.pexels_api_key,
}.items() if not v]
if faltan:
    print("FALTAN claves:", ", ".join(faltan)); sys.exit(1)
print("Claves OK. Voz:", cfg.elevenlabs_voice_id)
PY

# 5) Crear el video del tema indicado
echo "== Generando video para: $TEMA =="
python3 -m youtube_pipeline.create_video "$TEMA"

echo ""
echo "== LISTO =="
