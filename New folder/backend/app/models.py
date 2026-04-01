from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl


class AnalyzeUrlRequest(BaseModel):
    media_url: HttpUrl
    media_type: Literal["image", "video"]
    page_url: str | None = None
    context_text: str | None = None


class EvidenceItem(BaseModel):
    analyzer: str
    score: float = Field(ge=0.0, le=1.0)
    summary: str
    family: str = "heuristic"
    provider: str = "local"
    details: dict[str, Any] = Field(default_factory=dict)


class AnalysisResponse(BaseModel):
    verdict: Literal["likely_authentic", "possibly_manipulated", "highly_suspicious", "insufficient_evidence"]
    authenticity_score: float = Field(ge=0.0, le=1.0)
    suspicious_score: float = Field(ge=0.0, le=1.0)
    confidence: Literal["low", "medium", "high"]
    media_type: Literal["image", "video"]
    source: str
    summary: str
    evidence: list[EvidenceItem]
    notes: list[str]
    pipeline: list[str]
    fingerprint: str | None = None
