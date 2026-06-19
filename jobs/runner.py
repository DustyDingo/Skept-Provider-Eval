from __future__ import annotations

import asyncio

from providers.base import ProviderResult
from providers.resemble import ResembleProvider
from providers.aurigin import AuriginProvider
from providers.sightengine import SightengineProvider
from providers.reality_defender import RealityDefenderProvider

_PROVIDERS = [
    ResembleProvider(),
    AuriginProvider(),
    SightengineProvider(),
    RealityDefenderProvider(),
]


async def run_all_providers(paths: dict) -> list[ProviderResult]:
    audio_path = paths.get("audio")
    video_path = paths.get("video")

    nested = await asyncio.gather(
        *[p.analyse(audio_path, video_path) for p in _PROVIDERS],
        return_exceptions=False,
    )

    flat: list[ProviderResult] = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(item)
    return flat
