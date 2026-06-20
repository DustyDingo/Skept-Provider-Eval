from __future__ import annotations

import asyncio
import os
import time

import httpx

from providers.base import BaseProvider, ProviderResult

_API_KEY = os.getenv("REALITY_DEFENDER_API_KEY")
_BASE = "https://api.prd.realitydefender.xyz"


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
                # Step 1: request presigned URL
                presign_resp = await client.post(
                    f"{_BASE}/api/files/aws-presigned",
                    headers={"X-API-KEY": _API_KEY, "Content-Type": "application/json"},
                    json={"fileName": filename},
                )
                presign_resp.raise_for_status()
                presign_data = presign_resp.json()
                signed_url = presign_data.get("signedUrl")
                request_id = presign_data.get("requestId")
                if not signed_url:
                    return ProviderResult(
                        provider="reality_defender", modality=modality,
                        raw_score=None, normalised_score=None, label=None,
                        latency_ms=int((time.time() - t0) * 1000),
                        error=f"no signedUrl in presign response: {presign_data}",
                    )

                # Step 2: upload file to S3
                with open(path, "rb") as f:
                    put_resp = await client.put(signed_url, content=f.read())
                put_resp.raise_for_status()

                if not request_id:
                    return ProviderResult(
                        provider="reality_defender", modality=modality,
                        raw_score=None, normalised_score=None, label=None,
                        latency_ms=int((time.time() - t0) * 1000),
                        error=f"no requestId in presign response: {presign_data}",
                    )

                # Step 3: poll for results (max 60s)
                for _ in range(20):
                    await asyncio.sleep(3)
                    result_resp = await client.get(
                        f"{_BASE}/api/media/users/{request_id}",
                        headers={"X-API-KEY": _API_KEY},
                    )
                    if result_resp.status_code == 404:
                        continue
                    result_resp.raise_for_status()
                    data = result_resp.json()
                    final_score = (
                        (data.get("resultsSummary") or {})
                        .get("metadata", {})
                        .get("finalScore")
                    )
                    if final_score is not None:
                        raw = float(final_score) / 100.0
                        normalised = max(0.0, min(1.0, raw))
                        label = data.get("label") or ("fake" if normalised > 0.5 else "authentic")
                        return ProviderResult(
                            provider="reality_defender", modality=modality,
                            raw_score=float(final_score), normalised_score=normalised, label=label,
                            latency_ms=int((time.time() - t0) * 1000),
                            error=None,
                        )

                return ProviderResult(
                    provider="reality_defender", modality=modality,
                    raw_score=None, normalised_score=None, label=None,
                    latency_ms=int((time.time() - t0) * 1000),
                    error="polling timeout — no result after 60s",
                )
        except Exception as exc:
            return ProviderResult(
                provider="reality_defender", modality=modality,
                raw_score=None, normalised_score=None, label=None,
                latency_ms=int((time.time() - t0) * 1000),
                error=str(exc),
            )
