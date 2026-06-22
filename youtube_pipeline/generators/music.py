"""
Generación de una cama de música ambiental (pad) con FFmpeg, sin depender de
archivos externos ni red. Sirve como sonido de fondo suave bajo la narración.

Si prefieres música real, deja un archivo .mp3/.wav en youtube_pipeline/assets/music
y el pipeline lo usará en lugar de esta cama sintetizada.
"""

import subprocess
from pathlib import Path


def generate_music_bed(out_path: Path, duration: float = 40.0) -> Path:
    """
    Crea un pad ambiental cálido (acorde de La menor con notas detenidas, trémolo
    lento, eco y filtros) de `duration` segundos. El ensamblador lo repite en bucle
    a bajo volumen bajo la voz, así que con ~40 s basta.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    D = duration
    # Notas del acorde (Am): A2, C3, E3, A3, C4
    freqs = [110.0, 130.81, 164.81, 220.0, 261.63]
    inputs = []
    for f in freqs:
        inputs += ["-f", "lavfi", "-i", f"sine=frequency={f}:duration={D}"]
    mix_in = "".join(f"[{i}]" for i in range(len(freqs)))
    filt = (
        f"{mix_in}amix=inputs={len(freqs)}:normalize=1,"
        "tremolo=f=0.12:d=0.6,"
        "aecho=0.8:0.85:80:0.35,"
        "highpass=f=70,lowpass=f=1100,"
        "volume=3.0,"
        f"afade=t=in:st=0:d=2.5,afade=t=out:st={max(0.0, D-2.5):.2f}:d=2.5[a]"
    )
    cmd = ["ffmpeg", "-y", *inputs,
           "-filter_complex", filt, "-map", "[a]",
           "-ar", "48000", "-ac", "2", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"music_bed error: {result.stderr[-400:]}")
    return out_path
