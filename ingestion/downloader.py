from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

import yt_dlp


async def download(url: str) -> dict:
    job_dir = Path(f"/tmp/eval_{uuid.uuid4().hex}")
    job_dir.mkdir(parents=True, exist_ok=True)

    video_path = job_dir / "video.mp4"
    audio_path = job_dir / "audio.wav"

    ydl_opts: dict = {
        "outtmpl": str(video_path),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
    }
    if "tiktok.com" in url:
        ydl_opts["impersonate"] = "chrome"

    def _ydl_download() -> None:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    await asyncio.to_thread(_ydl_download)

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", str(video_path),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "1",
        str(audio_path), "-y",
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await proc.wait()

    return {
        "video": str(video_path) if video_path.exists() else None,
        "audio": str(audio_path) if audio_path.exists() else None,
        "dir": str(job_dir),
    }


def cleanup(paths: dict) -> None:
    job_dir = paths.get("dir")
    if job_dir:
        shutil.rmtree(job_dir, ignore_errors=True)
