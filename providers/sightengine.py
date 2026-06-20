from __future__ import annotations

import asyncio
import os
import time

import httpx

from providers.base import BaseProvider, ProviderResult

_API_USER = os.getenv("SIGHTENGINE_API_USER")
_API_SECRET = os.getenv("SIGHTENGINE_API_SECRET")


class SightengineProvider(BaseProvider):
    async def analyse(
        self,
        audio_path: str | None,
        video_path: str | None,
    ) -> list[ProviderResult]:
        if not video_path:
            return []
        return [await self._analyse_video(video_path)]

    async def _analyse_video(self, video_path: str) -> ProviderResult:
        t0 = time.time()
        if not _API_USER or not _API_SECRET:
            return ProviderResult(
                provider="sightengine", modality="synthetic",
                raw_score=None, normalised_score=None, label=None,
                latency_ms=0, error="API key not configured",
            )
        frame_path = video_path.replace(".mp4", "_frame.jpg")
        try:
            # Extract first frame for image-based genai detection (free tier)
            proc = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", video_path, "-vframes", "1", "-q:v", "2", frame_path, "-y",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.wait()

            if not os.path.exists(frame_path):
                return ProviderResult(
                    provider="sightengine", modality="synthetic",
                    raw_score=None, normalised_score=None, label=None,
                    latency_ms=int((time.time() - t0) * 1000),
                    error="failed to extract frame from video",
                )

            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(frame_path, "rb") as f:
                    resp = await client.post(
                        "https://api.sightengine.com/1.0/check.json",
                        data={
                            "models": "genai",
                            "api_user": _API_USER,
                            "api_secret": _API_SECRET,
                        },
                        files={"media": ("frame.jpg", f, "image/jpeg")},
                    )
                resp.raise_for_status()
                data = resp.json()

            raw = (data.get("genai") or {}).get("prob")
            if raw is None:
                raw = (data.get("genai") or {}).get("score")
            if raw is None:
                return ProviderResult(
                    provider="sightengine", modality="synthetic",
                    raw_score=None, normalised_score=None, label=None,
                    latency_ms=int((time.time() - t0) * 1000),
                    error=f"no genai.prob in response: {data}",
                )
            normalised = max(0.0, min(1.0, float(raw)))
            return ProviderResult(
                provider="sightengine", modality="synthetic",
                raw_score=float(raw), normalised_score=normalised,
                label="synthetic" if normalised > 0.5 else "authentic",
                latency_ms=int((time.time() - t0) * 1000),
                error=None,
            )
        except Exception as exc:
            return ProviderResult(
                provider="sightengine", modality="synthetic",
                raw_score=None, normalised_score=None, label=None,
                latency_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )
        finally:
            if os.path.exists(frame_path):
                os.unlink(frame_path)
