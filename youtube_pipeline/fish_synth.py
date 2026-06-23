# -*- coding: utf-8 -*-
"""
Generador de voz con Fish Speech / OpenAudio S2-pro. SE EJECUTA EN .venv-fish.

No se llama directamente: `producir.py` (en .venv-voz) lo invoca por subproceso
cuando `--voz fish`, pasándole un JSON con la referencia, los parámetros y la
lista de segmentos. Carga el modelo de 9 GB UNA sola vez y genera todos los
audios, aplicando velocidad (atempo) y recorte de silencios para pausas naturales.

JSON de entrada:
{
  "ckpt": "...checkpoints/s2-pro", "ref_wav": "...", "ref_text": "...",
  "temperature": 0.9, "top_p": 0.8, "repetition_penalty": 1.1, "seed": 1,
  "atempo": 1.07,
  "items": [{"path": "...seg_000.wav", "text": "[super happy] ..."}, ...]
}
"""
import sys, json, subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "fish-speech-src"))

import numpy as np
import soundfile as sf
import torch
from fish_speech.models.text2semantic.inference import launch_thread_safe_queue
from fish_speech.models.dac.inference import load_model as load_decoder_model
from fish_speech.inference_engine import TTSInferenceEngine
from fish_speech.utils.schema import ServeTTSRequest, ServeReferenceAudio


def _filter(atempo: float) -> str:
    # Velocidad + recorte de silencios de inicio/fin (pausas naturales).
    return (f"atempo={atempo},"
            "silenceremove=start_periods=1:start_silence=0.08:start_threshold=-45dB,areverse,"
            "silenceremove=start_periods=1:start_silence=0.12:start_threshold=-45dB,areverse")


def main(cfg_path: str):
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    ckpt = cfg["ckpt"]
    ref_bytes = Path(cfg["ref_wav"]).read_bytes()
    ref_text = cfg["ref_text"]
    seed = int(cfg.get("seed", 1))
    atempo = float(cfg.get("atempo", 1.07))
    temp = float(cfg.get("temperature", 0.9))
    top_p = float(cfg.get("top_p", 0.8))
    rep = float(cfg.get("repetition_penalty", 1.1))

    prec = torch.bfloat16
    print("  [fish] cargando S2-pro (una vez)...", flush=True)
    llama_queue = launch_thread_safe_queue(checkpoint_path=ckpt, device="cuda", precision=prec, compile=False)
    decoder = load_decoder_model(config_name="modded_dac_vq", checkpoint_path=ckpt + r"\codec.pth", device="cuda")
    engine = TTSInferenceEngine(llama_queue=llama_queue, decoder_model=decoder, precision=prec, compile=False)
    print("  [fish] modelo listo.", flush=True)

    def synth(text):
        req = ServeTTSRequest(
            text=text, references=[ServeReferenceAudio(audio=ref_bytes, text=ref_text)],
            temperature=temp, top_p=top_p, repetition_penalty=rep,
            # 4096 evita truncar bloques largos (1024 ≈ 44s cortaba la narración);
            # max_seq_len del modelo es 32768, así que hay margen de sobra.
            max_new_tokens=4096, chunk_length=200, format="wav", normalize=True, seed=seed)
        sr, segs, final = None, [], None
        for r in engine.inference(req):
            if r.code == "error":
                raise RuntimeError(str(r.error))
            if isinstance(r.audio, tuple):
                sr = r.audio[0]
                if r.code == "segment":
                    segs.append(np.asarray(r.audio[1]).flatten())
                elif r.code == "final":
                    final = np.asarray(r.audio[1]).flatten()
        return sr, (np.concatenate(segs) if segs else final)

    items = cfg["items"]
    for k, it in enumerate(items):
        out = Path(it["path"])
        out.parent.mkdir(parents=True, exist_ok=True)
        sr, audio = synth(it["text"])
        raw = out.with_suffix(".raw.wav")
        sf.write(str(raw), audio, sr)
        subprocess.run(["ffmpeg", "-y", "-i", str(raw), "-filter:a", _filter(atempo), str(out)],
                       check=True, capture_output=True)
        raw.unlink()
        print(f"  [fish] {k+1}/{len(items)} {out.name}", flush=True)
    print("  [fish] OK", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
