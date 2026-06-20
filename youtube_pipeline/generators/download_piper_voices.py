"""
Descarga voces de Piper TTS en español desde releases de GitHub.
(HuggingFace suele estar bloqueado en entornos con allowlist; GitHub no.)

Uso:
  python -m youtube_pipeline.generators.download_piper_voices
"""

import sys
import tarfile
import tempfile
from pathlib import Path
import requests

from ..config import cfg

VOICES_DIR = cfg.assets_dir / "piper_voices"

# Voces alojadas como assets de release en github.com/rhasspy/piper (v0.0.2)
GITHUB_VOICES = {
    "es-carlfm-x-low": "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-carlfm-x-low.tar.gz",
    "es-mls_10246-low": "https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-es-mls_10246-low.tar.gz",
}


def download_voice(name: str, url: str) -> bool:
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    onnx_path = VOICES_DIR / f"{name}.onnx"
    if onnx_path.exists():
        print(f"  ✓ {name} ya existe")
        return True

    print(f"  Descargando {name}...")
    try:
        resp = requests.get(url, stream=True, timeout=120)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            for chunk in resp.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name

        with tarfile.open(tmp_path, "r:gz") as tar:
            tar.extractall(VOICES_DIR)
        Path(tmp_path).unlink(missing_ok=True)
        print(f"  ✓ {name} listo")
        return True
    except Exception as e:
        print(f"  ✗ {name} falló: {e}")
        return False


def main():
    print("Descargando voces de Piper (español) desde GitHub...")
    ok = sum(download_voice(n, u) for n, u in GITHUB_VOICES.items())
    print(f"\n{ok}/{len(GITHUB_VOICES)} voces disponibles en {VOICES_DIR}")
    if ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
