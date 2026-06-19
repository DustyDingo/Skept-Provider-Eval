from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProviderResult:
    provider: str
    modality: str          # "audio" | "video" | "synthetic"
    raw_score: float | None
    normalised_score: float | None   # always 0.0–1.0, higher = more suspicious
    label: str | None      # provider's own label if available
    latency_ms: int
    error: str | None


class BaseProvider(ABC):
    @abstractmethod
    async def analyse(
        self,
        audio_path: str | None,
        video_path: str | None,
    ) -> list[ProviderResult]:
        ...
