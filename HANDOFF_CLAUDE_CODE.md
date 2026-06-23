# 🤝 Continuidad — Voz propia clonada (handoff para Claude Code local)

> Este documento resume una sesión previa (Claude Code en la web) para que el
> Claude Code de VS Code continúe sin perder contexto. Lee esto primero.

## Objetivo del usuario
Dejar de pagar la API de ElevenLabs y narrar los videos con **su propia voz
clonada**, automatizada, con calidad cercana a ElevenLabs. Es su canal, su voz.

## Hardware del usuario
- Windows, **GPU NVIDIA RTX 5090 (32 GB)** → arquitectura Blackwell `sm_120`.
- Python 3.11.9 (`py -3.11`), git y ffmpeg ya instalados y verificados.
- Edita/ejecuta en VS Code. La GPU está en su máquina (este pipeline corre local).

## Decisión técnica
- Motor elegido: **XTTS-v2 vía `coqui-tts`** (mejor balance español + clonación
  + facilidad). Alternativas futuras: F5-TTS / Fish Speech (mismo "enchufe").
- **Clave RTX 50:** PyTorch debe ser **cu128** (CUDA 12.8+); cu121/cu124 fallan.

## Lo que YA se implementó y se subió a esta rama
- `youtube_pipeline/generators/voiceover_local.py` — motor XTTS (carga el modelo
  una sola vez; registra *safe globals* para torch ≥2.6; salida `.wav`).
- `youtube_pipeline/generators/voiceover_elevenlabs.py` — el código original de
  ElevenLabs, intacto.
- `youtube_pipeline/generators/voiceover.py` — **selector** según `TTS_PROVIDER`
  (`elevenlabs` por defecto | `local`). Expone `active_provider()`.
- `youtube_pipeline/config.py` — campos `tts_provider`, `local_voice_sample`,
  `local_tts_model`, `local_tts_language`, `local_tts_device`.
- `youtube_pipeline/main.py` — `check_env()` ya no exige ELEVENLABS_API_KEY en
  modo local (exige que exista la muestra de voz); el log `[2/4]` es dinámico.
- `youtube_pipeline/.env.example` — variables nuevas documentadas.
- `youtube_pipeline/requirements-voz.txt` — deps del venv de voz.
- `SETUP_VOZ_LOCAL.md` — guía de instalación paso a paso para Windows + RTX.
- `youtube_pipeline/assets/voces/GUION_VOZ_REFERENCIA.md` — guion para grabar.

## Qué le falta hacer al usuario (estado actual)
1. ⏳ Grabar su voz con el guion (`GUION_VOZ_REFERENCIA.md`) desde DaVinci
   (con su EQ, sin reverb) y convertirla a `assets/voces/mi_voz.wav`.
2. ⏳ Crear el venv `.venv-voz` (Py 3.11) e instalar torch **cu128** + coqui-tts
   (Pasos 1–3 de SETUP_VOZ_LOCAL.md).
3. ⏳ Prueba rápida (Paso 5) y luego `TTS_PROVIDER=local` en `.env` (Paso 6).

## Cómo continuar (para el Claude local)
- Acompaña al usuario ejecutando los comandos de `SETUP_VOZ_LOCAL.md` en su PC
  y depurando errores en vivo (tienes terminal local; la sesión web no).
- Verifica primero `torch.cuda.is_available()` == True con `+cu128`.
- Cuando la prueba suene bien, corre un video corto con `--duration 120` y
  ajusta calidad (muestra de voz primero).

## Notas
- No borrar nada de ElevenLabs: es el respaldo.
- El assembler usa `ffprobe` para medir duración → acepta `.wav` sin cambios.
