"""
Final video assembler — orchestrates all editing steps into a publish-ready video.

Flow per segment:
  1. footage clip (trimmed/scaled to segment duration)
  2. voiceover audio (replaces or mixes with footage audio)
→ concat all segments
  3. add background music (low volume)
  4. burn subtitles
  5. add intro title card
  6. add outro CTA card
  7. add channel watermark
  8. export with YouTube-optimal settings
"""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from ..config import cfg
from .video_editor import (
    trim_video, scale_video, add_audio_to_video,
    add_background_music, concatenate_videos,
    add_subtitles, add_text_overlay, add_fade,
    add_logo_watermark, export_final, get_video_info,
)
from .captions import segments_to_srt


def _check_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def assemble_video(
    script,                          # VideoScript dataclass
    footage_paths: list[Optional[Path]],
    audio_paths: list[Path],
    output_dir: Path,
    music_path: Optional[Path] = None,
    logo_path: Optional[Path] = None,
    is_shorts: bool = False,
    burn_captions: bool = True,
    add_title_card: bool = True,
) -> Path:
    """
    Full assembly pipeline. Returns path to the final MP4.

    add_title_card: si False, no superpone el título arriba (útil cuando ya
    existe una pantalla de bienvenida/branding al inicio).
    """
    if not _check_ffmpeg():
        raise EnvironmentError(
            "FFmpeg not found. Install it: https://ffmpeg.org/download.html  "
            "or: sudo apt install ffmpeg"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "_work"
    work_dir.mkdir(exist_ok=True)

    width = cfg.shorts_width if is_shorts else cfg.video_width
    height = cfg.shorts_height if is_shorts else cfg.video_height
    segments = script.segments

    print(f"\n[assembler] Building {'Shorts' if is_shorts else 'video'}: {script.title}")
    print(f"  Segments: {len(segments)} | Clips: {len(footage_paths)} | Audio: {len(audio_paths)}")

    # ── Step 1: prepare each segment clip ──────────────────────────────────
    segment_clips = []
    for i, (segment, footage, audio) in enumerate(
        zip(segments, footage_paths, audio_paths)
    ):
        step = f"seg{i:03d}"
        target_dur = segment.get("duration_seconds", 10)

        if not audio or not audio.exists():
            print(f"  [skip] Segment {i} — missing audio")
            continue

        # Determine actual audio duration via ffprobe
        try:
            result = subprocess.run(
                ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(audio)],
                capture_output=True, text=True,
            )
            audio_dur = float(result.stdout.strip())
        except Exception:
            audio_dur = target_dur

        # Use footage if available, otherwise generate a black frame
        if footage and footage.exists():
            info = get_video_info(footage)
            clip_raw = work_dir / f"{step}_raw.mp4"

            if info["duration"] >= audio_dur:
                trim_video(footage, clip_raw, start=0, duration=audio_dur)
            else:
                # Loop the short clip to cover the audio
                loops = int(audio_dur / info["duration"]) + 1
                looped = work_dir / f"{step}_looped.mp4"
                subprocess.run([
                    "ffmpeg", "-y",
                    "-stream_loop", str(loops),
                    "-i", str(footage),
                    "-t", str(audio_dur),
                    "-c:v", "libx264", "-c:a", "aac",
                    str(looped),
                ], capture_output=True)
                trim_video(looped, clip_raw, start=0, duration=audio_dur)
        else:
            # Black placeholder with channel color
            clip_raw = work_dir / f"{step}_raw.mp4"
            subprocess.run([
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c={cfg.secondary_color.lstrip('#')}:size={width}x{height}:rate={cfg.video_fps}:duration={audio_dur}",
                "-c:v", "libx264",
                str(clip_raw),
            ], capture_output=True)

        # Scale to target resolution
        clip_scaled = work_dir / f"{step}_scaled.mp4"
        scale_video(clip_raw, clip_scaled, width, height)

        # Replace audio with voiceover
        clip_with_audio = work_dir / f"{step}_audio.mp4"
        add_audio_to_video(clip_scaled, audio, clip_with_audio, replace_original=True)

        segment_clips.append(clip_with_audio)
        print(f"  Segment {i+1}/{len(segments)} assembled ({audio_dur:.1f}s)")

    if not segment_clips:
        raise RuntimeError("No segments could be assembled.")

    # ── Step 2: concatenate all segments ───────────────────────────────────
    print("[assembler] Concatenating segments...")
    concat_path = work_dir / "concat.mp4"
    concatenate_videos(segment_clips, concat_path)

    current = concat_path

    # ── Step 3: background music ────────────────────────────────────────────
    if music_path and music_path.exists():
        print("[assembler] Adding background music...")
        music_path_out = work_dir / "with_music.mp4"
        add_background_music(current, music_path, music_path_out, music_volume=0.12)
        current = music_path_out

    # ── Step 4: subtitles ───────────────────────────────────────────────────
    if burn_captions and audio_paths:
        print("[assembler] Generating subtitles...")
        srt_path = work_dir / "captions.srt"
        try:
            srt_path = segments_to_srt(segments, audio_paths, srt_path)
            captioned = work_dir / "captioned.mp4"
            add_subtitles(current, srt_path, captioned)
            current = captioned
        except Exception as e:
            print(f"  [warn] Subtitles failed: {e} — continuing without captions")

    # ── Step 5: intro title card (optional) ─────────────────────────────────
    if add_title_card:
        print("[assembler] Adding title card...")
        titled = work_dir / "titled.mp4"
        safe_title = script.title.replace("'", "\\'").replace(":", "-")[:40]
        add_text_overlay(
            current, titled,
            text=safe_title,
            y="h*0.05",
            font_size=52 if not is_shorts else 40,
            start=0,
            end=5,
        )
        current = titled

    # ── Step 6: fade in/out ─────────────────────────────────────────────────
    faded = work_dir / "faded.mp4"
    add_fade(current, faded, fade_in=0.7, fade_out=0.7)
    current = faded

    # ── Step 7: logo watermark ──────────────────────────────────────────────
    if logo_path and logo_path.exists():
        print("[assembler] Adding watermark...")
        watermarked = work_dir / "watermarked.mp4"
        add_logo_watermark(current, logo_path, watermarked)
        current = watermarked

    # ── Step 8: final export ─────────────────────────────────────────────────
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in script.title[:50])
    final_path = output_dir / f"{safe_name}_FINAL.mp4"

    print("[assembler] Exporting final video...")
    export_final(current, final_path, width=width, height=height)

    # Clean up work files
    shutil.rmtree(work_dir, ignore_errors=True)

    file_size_mb = final_path.stat().st_size / 1_048_576
    print(f"\n[assembler] Done! → {final_path} ({file_size_mb:.1f} MB)")
    return final_path
