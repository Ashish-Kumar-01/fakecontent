from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AnalysisContext:
    media_bytes: bytes
    media_type: str
    source: str
    page_url: str | None = None
    context_text: str | None = None
    media_url: str | None = None
    temp_video_path: Path | None = None


@dataclass
class ProviderResult:
    analyzer: str
    score: float
    summary: str
    details: dict[str, Any] = field(default_factory=dict)
    family: str = "heuristic"
    provider: str = "local"


class AnalyzerProvider:
    name = "base"

    def supports(self, context: AnalysisContext) -> bool:
        return True

    def analyze(self, context: AnalysisContext) -> list[ProviderResult]:
        raise NotImplementedError
