from __future__ import annotations

import asyncio
import logging
import traceback

from providers.base import ProviderResult

logger = logging.getLogger(__name__)
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

    try:
        nested = await asyncio.gather(
            *[p.analyse(audio_path, video_path) for p in _PROVIDERS],
            return_exceptions=False,
        )
    except Exception:
        logger.error(f"runner.run_all_providers error: {traceback.format_exc()}")
        raise

    flat: list[ProviderResult] = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(item)
    return flat
