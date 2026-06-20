"""
FFmpeg-based video editing engine.
All operations use subprocess calls to ffmpeg for maximum compatibility.
"""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional

from ..config import cfg


def _run(cmd: list[str], description: str = "") -> subprocess.CompletedProcess:
    """Run an ffmpeg command and raise on failure."""
    print(f"  [ffmpeg] {description or ' '.join(cmd[:4])}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg error: {result.stderr[-500:]}")
    return result


def get_video_info(path: Path) -> dict:
    """Return duration, width, height, fps for a video file."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "quiet", "-print_format", "json",
            "-show_streams", "-show_format", str(path),
        ],
        capture_output=True, text=True,
    )
    data = json.loads(result.stdout)
    video_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "video"), {}
    )
    audio_stream = next(
        (s for s in data.get("streams", []) if s.get("codec_type") == "audio"), {}
    )
    fps_str = video_stream.get("r_frame_rate", "30/1")
    num, den = fps_str.split("/")
    fps = float(num) / float(den)
    return {
        "duration": float(data.get("format", {}).get("duration", 0)),
        "width": int(video_stream.get("width", 1920)),
        "height": int(video_stream.get("height", 1080)),
        "fps": fps,
        "has_audio": bool(audio_stream),
    }


def trim_video(input_path: Path, output_path: Path, start: float, duration: float) -> Path:
    """Trim a video to [start, start+duration]."""
    _run([
        "ffmpeg", "-y",
        "-ss", str(start), "-t", str(duration),
        "-i", str(input_path),
        "-c:v", "libx264", "-c:a", "aac",
        "-avoid_negative_ts", "make_zero",
        str(output_path),
    ], f"trim {input_path.name} -> {duration}s")
    return output_path


def scale_video(
    input_path: Path,
    output_path: Path,
    width: int,
    height: int,
    pad_color: str = "black",
) -> Path:
    """
    Scale and pad a video to exact dimensions.
    Pads instead of cropping to avoid cutting content.
    """
    _run([
        "ffmpeg", "-y", "-i", str(input_path),
        "-vf", (
            f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color={pad_color}"
        ),
        "-c:v", "libx264", "-c:a", "aac",
        str(output_path),
    ], f"scale to {width}x{height}")
    return output_path


def add_audio_to_video(
    video_path: Path,
    audio_path: Path,
    output_path: Path,
    replace_original: bool = True,
) -> Path:
    """Mix or replace the audio track of a video with a new audio file."""
    if replace_original:
        # Replace audio entirely
        _run([
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            str(output_path),
        ], "replace audio")
    else:
        # Mix original audio + new audio
        _run([
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-i", str(audio_path),
            "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "copy", "-c:a", "aac",
            str(output_path),
        ], "mix audio")
    return output_path


def add_background_music(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    music_volume: float = 0.15,
    voiceover_volume: float = 1.0,
) -> Path:
    """Add background music under the voiceover, ducking it appropriately."""
    _run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(music_path),
        "-filter_complex", (
            f"[0:a]volume={voiceover_volume}[v];"
            f"[1:a]volume={music_volume},aloop=loop=-1:size=2e+09[m];"
            "[v][m]amix=inputs=2:duration=first[a]"
        ),
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac",
        str(output_path),
    ], "add background music")
    return output_path


def concatenate_videos(input_paths: list[Path], output_path: Path) -> Path:
    """Concatenate a list of video files using FFmpeg concat filter."""
    if not input_paths:
        raise ValueError("No input videos to concatenate")
    if len(input_paths) == 1:
        shutil.copy2(input_paths[0], output_path)
        return output_path

    # Write a concat list file
    list_path = output_path.parent / "_concat_list.txt"
    with open(list_path, "w") as f:
        for p in input_paths:
            f.write(f"file '{p.resolve()}'\n")

    _run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_path),
        "-c:v", "libx264", "-c:a", "aac",
        str(output_path),
    ], f"concatenate {len(input_paths)} clips")

    list_path.unlink(missing_ok=True)
    return output_path


def add_subtitles(
    video_path: Path,
    srt_path: Path,
    output_path: Path,
    font_size: int = 18,
    font_color: str = "&H00FFFFFF",   # ASS = &HAABBGGRR (white)
    outline_color: str = "&H00000000",  # black
    position: str = "bottom",
    margin_v: int = 60,
) -> Path:
    """
    Burn subtitles into the video.

    Note on colors: libass uses the ASS format &HAABBGGRR (alpha-blue-green-red),
    NOT names like 'white'. Font size is in ASS script units (PlayResY default 288),
    so ~18 renders nicely on 1080p without overpowering the frame.
    """
    alignment = 2 if position == "bottom" else 8  # 2=bottom-center, 8=top-center
    _run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", (
            f"subtitles={srt_path}:force_style='"
            f"FontName=DejaVu Sans,FontSize={font_size},"
            f"PrimaryColour={font_color},OutlineColour={outline_color},"
            f"BorderStyle=1,Outline=2,Shadow=1,"
            f"Alignment={alignment},MarginV={margin_v}'"
        ),
        "-c:a", "copy",
        str(output_path),
    ], "burn subtitles")
    return output_path


def add_text_overlay(
    video_path: Path,
    output_path: Path,
    text: str,
    x: str = "(w-text_w)/2",
    y: str = "h*0.05",
    font_size: int = 48,
    font_color: str = "white",
    box_color: str = "black@0.5",
    start: float = 0,
    end: Optional[float] = None,
) -> Path:
    """Add a text overlay (title card, lower third, etc.)."""
    duration_filter = f":enable='between(t,{start},{end})'" if end else ""
    _run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", (
            f"drawtext=text='{text}'"
            f":fontsize={font_size}:fontcolor={font_color}"
            f":x={x}:y={y}"
            f":box=1:boxcolor={box_color}:boxborderw=10"
            f"{duration_filter}"
        ),
        "-c:a", "copy",
        str(output_path),
    ], f"add text: {text[:30]}")
    return output_path


def add_fade(
    video_path: Path,
    output_path: Path,
    fade_in: float = 0.5,
    fade_out: float = 0.5,
) -> Path:
    """Add fade-in and fade-out transitions."""
    info = get_video_info(video_path)
    duration = info["duration"]
    fade_out_start = duration - fade_out

    _run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"fade=t=in:st=0:d={fade_in},fade=t=out:st={fade_out_start:.2f}:d={fade_out}",
        "-af", f"afade=t=in:st=0:d={fade_in},afade=t=out:st={fade_out_start:.2f}:d={fade_out}",
        str(output_path),
    ], "add fade in/out")
    return output_path


def add_logo_watermark(
    video_path: Path,
    logo_path: Path,
    output_path: Path,
    position: str = "top_right",
    scale: float = 0.08,
    opacity: float = 0.7,
) -> Path:
    """Overlay a logo/watermark on the video."""
    positions = {
        "top_right": "W-w-20:20",
        "top_left": "20:20",
        "bottom_right": "W-w-20:H-h-20",
        "bottom_left": "20:H-h-20",
    }
    pos = positions.get(position, positions["top_right"])

    _run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(logo_path),
        "-filter_complex", (
            f"[1:v]scale=iw*{scale}:-1,format=rgba,"
            f"colorchannelmixer=aa={opacity}[logo];"
            f"[0:v][logo]overlay={pos}[v]"
        ),
        "-map", "[v]", "-map", "0:a?",
        "-c:a", "copy",
        str(output_path),
    ], f"add watermark at {position}")
    return output_path


def ken_burns(
    image_path: Path,
    output_path: Path,
    duration: float,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    zoom_start: float = 1.0,
    zoom_end: float = 1.12,
    direction: str = "in",
) -> Path:
    """
    Anima una imagen estática con un zoom/pan lento (efecto Ken Burns)
    para darle vida. Devuelve un clip de video de la duración pedida.
    """
    total_frames = int(duration * fps)
    if direction == "in":
        z_expr = f"min(zoom+{(zoom_end - zoom_start)/total_frames:.6f},{zoom_end})"
    else:
        z_expr = f"max(zoom-{(zoom_end - zoom_start)/total_frames:.6f},{zoom_start})"

    # Render a 2x para que el zoom no pixele, luego escala a destino
    _run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-vf", (
            f"scale={width*2}:{height*2},"
            f"zoompan=z='{z_expr}':d={total_frames}"
            f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":s={width}x{height}:fps={fps},"
            f"trim=duration={duration},setpts=PTS-STARTPTS"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-t", str(duration),
        str(output_path),
    ], f"ken burns {image_path.name} ({duration:.1f}s)")
    return output_path


def export_final(
    video_path: Path,
    output_path: Path,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    video_bitrate: str = "5000k",
    audio_bitrate: str = "192k",
) -> Path:
    """Export the final video with optimal settings for YouTube."""
    _run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-b:v", video_bitrate,
        "-c:a", "aac", "-b:a", audio_bitrate, "-ar", "48000",
        "-r", str(fps),
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        str(output_path),
    ], f"export final: {output_path.name}")
    return output_path
