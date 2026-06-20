"""
Video footage and photo sourcing from Pexels (free stock) and Higgsfield (AI-generated).
Each segment's visual_cue is used to find or generate relevant footage/photos.
"""

import os
import time
import json
import random
from pathlib import Path
from typing import Optional
import requests

from ..config import cfg


# ---------------------------------------------------------------------------
# Pexels — free stock video
# ---------------------------------------------------------------------------

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
PEXELS_POPULAR_URL = "https://api.pexels.com/videos/popular"
PEXELS_PHOTO_URL = "https://api.pexels.com/v1/search"


def search_pexels_video(
    query: str,
    per_page: int = 10,
    orientation: str = "landscape",
    min_duration: int = 5,
    max_duration: int = 60,
) -> Optional[dict]:
    """
    Search Pexels for a video matching the query.
    Returns the best matching video file info or None.
    """
    resp = requests.get(
        PEXELS_SEARCH_URL,
        params={
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": "large",
        },
        headers={"Authorization": cfg.pexels_api_key},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    videos = data.get("videos", [])

    # Filter by duration and pick the best HD file
    for video in videos:
        duration = video.get("duration", 0)
        if not (min_duration <= duration <= max_duration):
            continue
        # Pick highest quality file ≤ 1080p
        files = sorted(
            [f for f in video.get("video_files", []) if f.get("height", 0) >= 720],
            key=lambda f: f.get("height", 0),
            reverse=True,
        )
        if files:
            return {
                "url": files[0]["link"],
                "width": files[0].get("width", 1920),
                "height": files[0].get("height", 1080),
                "duration": duration,
                "source": "pexels",
                "video_id": video["id"],
            }
    return None


def search_pexels_photo(
    query: str,
    per_page: int = 5,
    orientation: str = "landscape",
) -> Optional[dict]:
    """
    Search Pexels for a photo matching the query.
    Returns metadata dict with 'url', 'width', 'height', 'photographer' or None.
    Uses the /v1/search photos endpoint (NOT the videos endpoint).
    """
    if not cfg.pexels_api_key:
        return None
    resp = requests.get(
        PEXELS_PHOTO_URL,
        params={
            "query": query,
            "per_page": per_page,
            "orientation": orientation,
            "size": "large",
        },
        headers={"Authorization": cfg.pexels_api_key},
        timeout=15,
    )
    resp.raise_for_status()
    photos = resp.json().get("photos", [])
    if not photos:
        return None
    photo = photos[0]
    src = photo.get("src", {})
    url = src.get("large2x") or src.get("large") or src.get("original")
    return {
        "url": url,
        "width": photo.get("width", 1920),
        "height": photo.get("height", 1080),
        "photographer": photo.get("photographer", ""),
    }


def download_photo(url: str, output_path: Path) -> Path:
    """Download a photo (JPEG/PNG) from a URL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    output_path.write_bytes(resp.content)
    return output_path


def download_video(url: str, output_path: Path) -> Path:
    """Download a video file from a URL."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return output_path


def fetch_segment_footage(
    segments: list[dict],
    output_dir: Path,
    is_shorts: bool = False,
    delay: float = 1.0,
) -> list[Optional[Path]]:
    """
    Fetch one footage clip for each segment using its visual_cue.
    Falls back to a generic query if the specific one returns nothing.
    Returns list of video paths (None if download failed).
    """
    orientation = "portrait" if is_shorts else "landscape"
    footage_paths = []

    for i, segment in enumerate(segments):
        visual_cue = segment.get("visual_cue", "")
        duration = segment.get("duration_seconds", 10)

        # Simplify complex cues to search-friendly queries (first ~5 words)
        search_query = " ".join(visual_cue.split()[:6]) if visual_cue else "technology abstract"
        out_path = output_dir / f"footage_{i:03d}.mp4"

        if out_path.exists():
            footage_paths.append(out_path)
            continue

        print(f"  [footage] Segment {i+1}: searching '{search_query}'...")

        video_info = search_pexels_video(
            search_query,
            orientation=orientation,
            min_duration=max(3, duration - 5),
            max_duration=duration + 15,
        )

        if not video_info:
            # Fallback: generic niche-related query
            video_info = search_pexels_video(
                "technology innovation",
                orientation=orientation,
            )

        if video_info:
            try:
                download_video(video_info["url"], out_path)
                footage_paths.append(out_path)
                print(f"    Downloaded: {out_path.name} ({video_info['duration']}s)")
            except Exception as e:
                print(f"    Download failed: {e}")
                footage_paths.append(None)
        else:
            print(f"    No footage found for segment {i+1}")
            footage_paths.append(None)

        time.sleep(delay)

    return footage_paths


# ---------------------------------------------------------------------------
# Higgsfield — AI-generated video
# ---------------------------------------------------------------------------

HIGGSFIELD_GENERATE_URL = "https://api.higgsfield.ai/v1/generate"
HIGGSFIELD_STATUS_URL = "https://api.higgsfield.ai/v1/jobs/{job_id}"


def generate_higgsfield_clip(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    output_path: Optional[Path] = None,
    poll_interval: int = 5,
    max_wait: int = 300,
) -> Optional[Path]:
    """
    Generate an AI video clip using Higgsfield API.
    Polls until the job completes, then downloads the result.
    """
    if not cfg.higgsfield_api_key:
        print("  [higgsfield] No API key set, skipping AI generation.")
        return None

    resp = requests.post(
        HIGGSFIELD_GENERATE_URL,
        json={
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
        },
        headers={
            "Authorization": f"Bearer {cfg.higgsfield_api_key}",
            "Content-Type": "application/json",
        },
        timeout=30,
    )
    resp.raise_for_status()
    job_id = resp.json()["job_id"]

    # Poll for completion
    waited = 0
    while waited < max_wait:
        time.sleep(poll_interval)
        waited += poll_interval

        status_resp = requests.get(
            HIGGSFIELD_STATUS_URL.format(job_id=job_id),
            headers={"Authorization": f"Bearer {cfg.higgsfield_api_key}"},
            timeout=15,
        )
        status_resp.raise_for_status()
        status_data = status_resp.json()

        state = status_data.get("status", "")
        if state == "completed":
            video_url = status_data["output_url"]
            if output_path:
                return download_video(video_url, output_path)
            return video_url
        if state in ("failed", "error"):
            print(f"  [higgsfield] Job failed: {status_data.get('error', 'unknown')}")
            return None

    print(f"  [higgsfield] Timed out after {max_wait}s")
    return None
