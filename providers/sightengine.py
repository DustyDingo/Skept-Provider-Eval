from __future__ import annotations

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
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(video_path, "rb") as f:
                    resp = await client.post(
                        "https://api.sightengine.com/1.0/video/check-sync.json",
                        data={
                            "models": "genai",
                            "api_user": _API_USER,
                            "api_secret": _API_SECRET,
                        },
                        files={"media": ("video.mp4", f, "video/mp4")},
                    )
                resp.raise_for_status()
                data = resp.json()

            raw = (data.get("genai") or {}).get("score")
            if raw is None:
                return ProviderResult(
                    provider="sightengine", modality="synthetic",
                    raw_score=None, normalised_score=None, label=None,
                    latency_ms=int((time.time() - t0) * 1000),
                    error=f"no ai_generated.score in response: {data}",
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
