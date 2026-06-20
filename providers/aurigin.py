from __future__ import annotations

import os
import time

import httpx

from providers.base import BaseProvider, ProviderResult

_API_KEY = os.getenv("AURIGIN_API_KEY")


class AuriginProvider(BaseProvider):
    async def analyse(
        self,
        audio_path: str | None,
        video_path: str | None,
    ) -> list[ProviderResult]:
        if not audio_path:
            return []
        return [await self._analyse_audio(audio_path)]

    async def _analyse_audio(self, audio_path: str) -> ProviderResult:
        t0 = time.time()
        if not _API_KEY:
            return ProviderResult(
                provider="aurigin", modality="audio",
                raw_score=None, normalised_score=None, label=None,
                latency_ms=0, error="API key not configured",
            )
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(audio_path, "rb") as f:
                    resp = await client.post(
                        "https://api.aurigin.ai/v1/predict",
                        headers={"x-api-key": _API_KEY},
                        files={"file": ("audio.wav", f, "audio/wav")},
                    )
                resp.raise_for_status()
                data = resp.json()

            raw = data.get("score")
            if raw is None:
                return ProviderResult(
                    provider="aurigin", modality="audio",
                    raw_score=None, normalised_score=None,
                    label=data.get("label"),
                    latency_ms=int((time.time() - t0) * 1000),
                    error=f"no score in response: {data}",
                )
            normalised = max(0.0, min(1.0, float(raw)))
            label = data.get("label") or ("fake" if normalised > 0.5 else "authentic")
            return ProviderResult(
                provider="aurigin", modality="audio",
                raw_score=float(raw), normalised_score=normalised, label=label,
                latency_ms=int((time.time() - t0) * 1000),
                error=None,
            )
        except Exception as exc:
            return ProviderResult(
                provider="aurigin", modality="audio",
                raw_score=None, normalised_score=None, label=None,
                latency_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )
