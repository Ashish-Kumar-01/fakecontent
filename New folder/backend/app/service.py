from __future__ import annotations

import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .analyzers import ProvenanceStore
from .models import AnalysisResponse, EvidenceItem
from .providers import AnalysisContext, ProviderResult, build_provider_stack


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PROVENANCE = ProvenanceStore(DATA_DIR / "history.json")
PROVIDERS = build_provider_stack()


def _confidence_from_score(score: float) -> str:
    if score >= 0.72 or score <= 0.2:
        return "high"
    if score >= 0.45 or score <= 0.35:
        return "medium"
    return "low"


def _verdict_from_authenticity(score: float) -> str:
    if score >= 0.75:
        return "likely_authentic"
    if score >= 0.45:
        return "possibly_manipulated"
    return "highly_suspicious"


def _summary_from_verdict(verdict: str, suspicious_score: float, evidence: list[EvidenceItem]) -> str:
    strongest = sorted(evidence, key=lambda item: item.score, reverse=True)[:2]
    top_signals = ", ".join(item.analyzer for item in strongest if item.score > 0.12)

    if verdict == "likely_authentic":
        return "Most analyzers found low manipulation risk signals."
    if verdict == "possibly_manipulated":
        return f"The media shows mixed signals with moderate risk concentrated in {top_signals or 'multiple analyzers'}."
    if suspicious_score > 0.85:
        return f"Multiple analyzers converged on strong manipulation risk, especially {top_signals or 'across the pipeline'}."
    return f"The system found substantial risk signals, led by {top_signals or 'several analyzers'}."


def fetch_media(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 FakeContentDetectionAssistant/1.0"})
    try:
        with urlopen(request, timeout=12) as response:
            return response.read()
    except (HTTPError, URLError) as exc:
        raise ValueError(f"Unable to fetch media from URL: {exc}") from exc


def analyze_bytes(
    media_bytes: bytes,
    media_type: str,
    source: str,
    page_url: str | None = None,
    context_text: str | None = None,
    media_url: str | None = None,
) -> AnalysisResponse:
    evidence: list[EvidenceItem] = []
    notes: list[str] = []
    suspicious_components: list[float] = []
    pipeline: list[str] = []

    provenance_score, provenance_summary, provenance_details, fingerprint = PROVENANCE.analyze(
        media_bytes, media_url, media_type
    )
    evidence.append(
        EvidenceItem(
            analyzer="provenance",
            score=provenance_score,
            summary=provenance_summary,
            family="provenance",
            provider="local",
            details=provenance_details,
        )
    )
    suspicious_components.append(provenance_score)
    pipeline.append("provenance")

    temp_path: Path | None = None
    if media_type == "video":
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_file.write(media_bytes)
            temp_path = Path(temp_file.name)

    context = AnalysisContext(
        media_bytes=media_bytes,
        media_type=media_type,
        source=source,
        page_url=page_url,
        context_text=context_text,
        media_url=media_url,
        temp_video_path=temp_path,
    )

    try:
        for provider in PROVIDERS:
            if not provider.supports(context):
                continue

            try:
                provider_results: list[ProviderResult] = provider.analyze(context)
            except Exception as exc:  # noqa: BLE001
                notes.append(f"Provider '{provider.name}' was skipped because it failed: {exc}")
                continue

            if not provider_results:
                continue

            pipeline.append(provider.name)
            for result in provider_results:
                evidence.append(
                    EvidenceItem(
                        analyzer=result.analyzer,
                        score=result.score,
                        summary=result.summary,
                        family=result.family,
                        provider=result.provider,
                        details=result.details,
                    )
                )
                suspicious_components.append(result.score)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)

    suspicious_score = min(1.0, sum(suspicious_components) / max(len(suspicious_components), 1) * 1.35)
    authenticity_score = round(1.0 - suspicious_score, 3)
    confidence = _confidence_from_score(authenticity_score)
    verdict = _verdict_from_authenticity(authenticity_score)
    summary = _summary_from_verdict(verdict, suspicious_score, evidence)

    if provenance_score > 0.2:
        notes.append("Matching content appeared previously from another source.")
    if any(item.analyzer == "context_risk" and item.score > 0.15 for item in evidence):
        notes.append("Nearby text uses virality-style language, which raises context risk.")
    if any(item.provider == "transformers" for item in evidence):
        notes.append("Transformer-backed model output is included in the score fusion.")
    if any(item.provider == "local_http_model" for item in evidence):
        notes.append("An external forensic model endpoint contributed additional evidence.")
    if media_type == "video":
        notes.append("Video analysis uses sampled frames for speed, so subtle edits may be missed.")
    else:
        notes.append("Image results should still be paired with source verification and provenance checks.")

    return AnalysisResponse(
        verdict=verdict,  # type: ignore[arg-type]
        authenticity_score=authenticity_score,
        suspicious_score=round(suspicious_score, 3),
        confidence=confidence,  # type: ignore[arg-type]
        media_type=media_type,  # type: ignore[arg-type]
        source=source,
        summary=summary,
        evidence=evidence,
        notes=notes,
        pipeline=pipeline,
        fingerprint=fingerprint,
    )
