"""
Generación de música con Mureka.ai (https://platform.mureka.ai).

Crea una pista INSTRUMENTAL a partir de un prompt de texto y la descarga como
MP3. Es asíncrono: se envía la tarea y se hace polling hasta que termina.

API usada (oficial):
  POST https://api.mureka.ai/v1/instrumental/generate   -> {"id", "status"}
  GET  https://api.mureka.ai/v1/instrumental/query/{id}  -> {"status", "choices":[{"url"...}]}
Auth: header  Authorization: Bearer <MUREKA_API_KEY>
"""

import time
from pathlib import Path
from typing import Optional
import requests

from ..config import cfg

BASE_URL = "https://api.mureka.ai"


def generate_music_mureka(
    out_path: Path,
    prompt: str = "calm cinematic background music, soft piano and warm pads, subtle, non-distracting, loopable",
    model: str = "auto",
    max_wait: int = 240,
    poll_interval: int = 6,
) -> Optional[Path]:
    """
    Genera una pista instrumental con Mureka y la guarda en out_path (MP3).
    Devuelve la ruta, o None si no hay API key. Lanza excepción si la API falla.
    """
    if not cfg.mureka_api_key:
        return None

    headers = {
        "Authorization": f"Bearer {cfg.mureka_api_key}",
        "Content-Type": "application/json",
    }

    # 1) Crear la tarea
    resp = requests.post(
        f"{BASE_URL}/v1/instrumental/generate",
        json={"model": model, "prompt": prompt},
        headers=headers, timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    task_id = data.get("id") or data.get("task_id") or (data.get("data") or {}).get("id")
    if not task_id:
        raise RuntimeError(f"Mureka: respuesta sin id de tarea: {str(data)[:200]}")

    # 2) Polling hasta que termine
    waited = 0
    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval
        q = requests.get(f"{BASE_URL}/v1/instrumental/query/{task_id}",
                         headers=headers, timeout=30)
        q.raise_for_status()
        body = q.json()
        body = body.get("data", body)  # algunos gateways envuelven en "data"
        status = body.get("status")
        if status == "succeeded":
            choices = body.get("choices") or []
            url = None
            if choices:
                c = choices[0]
                url = c.get("url") or c.get("mp3_url") or c.get("flac_url") or c.get("wav_url")
            if not url:
                raise RuntimeError(f"Mureka: terminó sin URL de audio: {str(body)[:200]}")
            # 3) Descargar
            audio = requests.get(url, timeout=180)
            audio.raise_for_status()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(audio.content)
            return out_path
        if status in ("failed", "timeouted", "cancelled"):
            raise RuntimeError(f"Mureka: tarea {status}: {str(body)[:200]}")

    raise RuntimeError(f"Mureka: tiempo de espera agotado ({max_wait}s)")
