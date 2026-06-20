from __future__ import annotations

import os
import time

import httpx

from providers.base import BaseProvider, ProviderResult

_API_KEY = os.getenv("REALITY_DEFENDER_API_KEY")
_BASE_URL = "https://api.realitydefender.com/api/upload"


class RealityDefenderProvider(BaseProvider):
    async def analyse(
        self,
        audio_path: str | None,
        video_path: str | None,
    ) -> list[ProviderResult]:
        results: list[ProviderResult] = []
        if audio_path:
            results.append(await self._upload("audio", audio_path, "audio/wav"))
        if video_path:
            results.append(await self._upload("video", video_path, "video/mp4"))
        return results

    async def _upload(self, modality: str, path: str, mime: str) -> ProviderResult:
        t0 = time.time()
        if not _API_KEY:
            return ProviderResult(
                provider="reality_defender", modality=modality,
                raw_score=None, normalised_score=None, label=None,
                latency_ms=0, error="API key not configured",
            )
        filename = "audio.wav" if modality == "audio" else "video.mp4"
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                with open(path, "rb") as f:
                    resp = await client.post(
                        _BASE_URL,
                        headers={"X-API-Key": _API_KEY},
                        files={"file": (filename, f, mime)},
                    )
                resp.raise_for_status()
                data = resp.json()

            raw = data.get("score") or (data.get("result") or {}).get("score")
            if raw is None:
                return ProviderResult(
                    provider="reality_defender", modality=modality,
                    raw_score=None, normalised_score=None,
                    label=data.get("label"),
                    latency_ms=int((time.time() - t0) * 1000),
                    error=f"no score in response: {data}",
                )
            normalised = max(0.0, min(1.0, float(raw)))
            label = data.get("label") or ("fake" if normalised > 0.5 else "authentic")
            return ProviderResult(
                provider="reality_defender", modality=modality,
                raw_score=float(raw), normalised_score=normalised, label=label,
                latency_ms=int((time.time() - t0) * 1000),
                error=None,
            )
        except Exception as exc:
            return ProviderResult(
                provider="reality_defender", modality=modality,
                raw_score=None, normalised_score=None, label=None,
                latency_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )
