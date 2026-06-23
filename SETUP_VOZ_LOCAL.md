# 🎙️ Setup de voz local (clonar TU voz, gratis) — Windows + NVIDIA

Reemplaza ElevenLabs por tu propia voz usando **XTTS-v2 (Coqui TTS)**.
Pensado para **Windows + GPU NVIDIA** (probado en RTX 5090, 32 GB).

> ElevenLabs sigue funcionando como respaldo. Solo cambias `TTS_PROVIDER`.

---

## Requisitos ya cubiertos
- ✅ git
- ✅ Python **3.11** (NO uses 3.12+ para esto; `py -3.11`)
- ✅ ffmpeg
- ✅ GPU NVIDIA con drivers recientes (`nvidia-smi`)

---

## Paso 1 — Entorno virtual aislado (Python 3.11)

Desde la carpeta del proyecto (`Videos_con_IA`):

```powershell
py -3.11 -m venv .venv-voz
.\.venv-voz\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

> Si `Activate.ps1` da error de *execution policy*, ejecuta una vez:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`
> y vuelve a activar.

La terminal debe empezar con `(.venv-voz)`.

---

## Paso 2 — PyTorch con CUDA 12.8 (¡clave para la RTX 50!)

La serie RTX 50 (Blackwell, `sm_120`) **necesita PyTorch con CUDA 12.8 o
superior**. Las ruedas viejas (cu121/cu124) fallan con "no kernel image".

```powershell
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu128
```

Verifica que vea la GPU:

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Debe imprimir algo como: `2.x.x+cu128 True NVIDIA GeForce RTX 5090`.
Si dice `False`, avísale a Claude antes de seguir.

---

## Paso 3 — Instalar el motor de voz (Coqui TTS)

```powershell
pip install coqui-tts
```

> `coqui-tts` es el fork mantenido de Coqui (la empresa cerró, el modelo sigue
> libre). Trae XTTS-v2. Si intenta bajar otra versión de torch, no pasa:
> la del Paso 2 manda mientras no la desinstale.

---

## Paso 4 — Preparar tu muestra de voz

1. Graba leyendo `youtube_pipeline/assets/voces/GUION_VOZ_REFERENCIA.md`
   (con tu EQ de DaVinci, **sin reverb**). Expórtala como `mi_voz_raw.wav`.
2. Conviértela al formato que el modelo prefiere (mono, 24 kHz, 16-bit) y
   recorta a los mejores ~60–90 s con ffmpeg:

```powershell
# Convertir (ajusta la ruta de entrada a donde tengas tu grabación)
ffmpeg -i mi_voz_raw.wav -ac 1 -ar 24000 -sample_fmt s16 youtube_pipeline/assets/voces/mi_voz.wav

# (Opcional) recortar, p.ej. del segundo 5 al 75:
# ffmpeg -i mi_voz_raw.wav -ss 5 -t 70 -ac 1 -ar 24000 -sample_fmt s16 youtube_pipeline/assets/voces/mi_voz.wav
```

El archivo final debe quedar en:
`youtube_pipeline/assets/voces/mi_voz.wav`

---

## Paso 5 — Prueba rápida (antes de tocar el pipeline)

Con el venv activo:

```powershell
$env:COQUI_TOS_AGREED="1"
python -c "from TTS.api import TTS; t=TTS('tts_models/multilingual/multi-dataset/xtts_v2').to('cuda'); t.tts_to_file(text='Hola, esta es mi voz clonada funcionando en mi propia computadora.', speaker_wav='youtube_pipeline/assets/voces/mi_voz.wav', language='es', file_path='prueba_voz.wav')"
```

La primera vez descarga ~2 GB (queda en caché). Al terminar, reproduce
`prueba_voz.wav`. ¿Suena a ti? 🎉 Entonces el motor está listo.

---

## Paso 6 — Activar la voz local en el pipeline

En tu archivo `youtube_pipeline/.env` (cópialo de `.env.example` si no existe):

```
TTS_PROVIDER=local
LOCAL_VOICE_SAMPLE=youtube_pipeline/assets/voces/mi_voz.wav
LOCAL_TTS_LANGUAGE=es
LOCAL_TTS_DEVICE=cuda
```

Y ejecuta el pipeline normal (con el venv `.venv-voz` activo):

```powershell
python -m youtube_pipeline.main --topic "Los 3 mejores modelos de IA en 2026" --duration 120
```

En el paso `[2/4]` debe decir **"Generating voiceovers with tu voz local (XTTS)"**.

Para volver a ElevenLabs en cualquier momento: `TTS_PROVIDER=elevenlabs`.

---

## Ajuste de calidad (cuando ya funcione)
- Si suena con ruido/eco → mejora la **muestra** (es lo que más impacta).
- Si corta raro frases largas → ya partimos por frases (`split_sentences`).
- ¿Quieres aún más naturalidad? Se puede migrar a **F5-TTS** o **Fish Speech**
  reusando el mismo "enchufe" (`voiceover_local.py`). Pídeselo a Claude.

## Problemas comunes
- `torch.cuda.is_available()` = False → instalaste torch sin cu128 (Paso 2).
- Error al cargar XTTS con torch 2.6+ → ya está resuelto en `voiceover_local.py`
  (registra los *safe globals*). Si aún falla, comparte el traceback.
- Voz en inglés con acento → revisa `LOCAL_TTS_LANGUAGE=es`.
