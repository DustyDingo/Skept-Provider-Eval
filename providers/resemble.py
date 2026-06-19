from __future__ import annotations

import os
import time

import httpx

from providers.base import BaseProvider, ProviderResult

_API_KEY = os.getenv("RESEMBLE_API_KEY")


class ResembleProvider(BaseProvider):
    async def analyse(
        self,
        audio_path: str | None,
        video_path: str | None,
    ) -> list[ProviderResult]:
        results: list[ProviderResult] = []
        if audio_path:
            results.append(await self._analyse_audio(audio_path))
        if video_path:
            results.append(self._stub_video())
        return results

    async def _analyse_audio(self, audio_path: str) -> ProviderResult:
        t0 = time.time()
        if not _API_KEY:
            return ProviderResult(
                provider="resemble", modality="audio",
                raw_score=None, normalised_score=None, label=None,
                latency_ms=0, error="API key not configured",
            )
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(audio_path, "rb") as f:
                    resp = await client.post(
                        "https://api.resemble.ai/v1/detect",
                        headers={"Authorization": f"Bearer {_API_KEY}"},
                        files={"audio_file": ("audio.wav", f, "audio/wav")},
                    )
                resp.raise_for_status()
                data = resp.json()

            raw = (data.get("metrics") or {}).get("aggregated_score")
            if raw is None:
                raw = data.get("aggregated_score")
            if raw is None:
                return ProviderResult(
                    provider="resemble", modality="audio",
                    raw_score=None, normalised_score=None, label=None,
                    latency_ms=int((time.time() - t0) * 1000),
                    error=f"no aggregated_score in response: {data}",
                )
            if raw == -1.0:
                return ProviderResult(
                    provider="resemble", modality="audio",
                    raw_score=raw, normalised_score=None, label=None,
                    latency_ms=int((time.time() - t0) * 1000),
                    error="aggregated_score=-1.0 (no signal)",
                )
            normalised = max(0.0, min(1.0, (raw + 1.0) / 2.0))
            return ProviderResult(
                provider="resemble", modality="audio",
                raw_score=raw, normalised_score=normalised,
                label="fake" if normalised > 0.5 else "authentic",
                latency_ms=int((time.time() - t0) * 1000),
                error=None,
            )
        except Exception as exc:
            return ProviderResult(
                provider="resemble", modality="audio",
                raw_score=None, normalised_score=None, label=None,
                latency_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )

    @staticmethod
    def _stub_video() -> ProviderResult:
        # TODO: wire Resemble video endpoint
        return ProviderResult(
            provider="resemble", modality="video",
            raw_score=None, normalised_score=None, label=None,
            latency_ms=0, error="video endpoint not yet implemented",
        )
