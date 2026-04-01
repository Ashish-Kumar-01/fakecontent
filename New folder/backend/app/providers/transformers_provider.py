from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image

from ..config import settings
from .base import AnalysisContext, AnalyzerProvider, ProviderResult


class TransformersProvider(AnalyzerProvider):
    name = "transformers"

    def __init__(self) -> None:
        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Transformers provider requested but transformers is not installed.") from exc

        self._image_pipeline = None
        self._multimodal_pipeline = None
        if settings.hf_image_model:
            self._image_pipeline = pipeline("image-classification", model=settings.hf_image_model)
        if settings.hf_multimodal_model:
            self._multimodal_pipeline = pipeline("image-to-text", model=settings.hf_multimodal_model)

    def supports(self, context: AnalysisContext) -> bool:
        return context.media_type == "image" and bool(self._image_pipeline or self._multimodal_pipeline)

    def analyze(self, context: AnalysisContext) -> list[ProviderResult]:
        image = Image.open(BytesIO(context.media_bytes)).convert("RGB")
        results: list[ProviderResult] = []

        if self._image_pipeline:
            classifier_output = self._image_pipeline(image)
            suspicious_score, top_label = _suspicious_score_from_classifier(classifier_output)
            results.append(
                ProviderResult(
                    analyzer="hf_image_classifier",
                    score=suspicious_score,
                    summary=f"Transformer classifier highlighted '{top_label}' as the leading visual signal.",
                    details={"raw_predictions": classifier_output[:3]},
                    family="forensics",
                    provider=self.name,
                )
            )

        if self._multimodal_pipeline:
            caption_output = self._multimodal_pipeline(image)
            generated = caption_output[0]["generated_text"] if caption_output else ""
            semantic_score = _semantic_risk_from_caption(generated, context.context_text)
            results.append(
                ProviderResult(
                    analyzer="hf_multimodal_reasoner",
                    score=semantic_score,
                    summary="Multimodal captioning compared the visible scene against the nearby page context.",
                    details={
                        "generated_caption": generated,
                        "caption_overlap_score": round(1.0 - semantic_score, 3),
                    },
                    family="multimodal",
                    provider=self.name,
                )
            )

        return results


def _suspicious_score_from_classifier(predictions: list[dict]) -> tuple[float, str]:
    if not predictions:
        return 0.0, "unknown"

    top = predictions[0]
    label = str(top.get("label", "unknown")).lower()
    score = float(top.get("score", 0.0))
    suspicious_keywords = ("fake", "synthetic", "deepfake", "manipulated", "edited", "generated")
    if any(keyword in label for keyword in suspicious_keywords):
        return min(1.0, 0.45 + score * 0.55), label
    return max(0.0, 0.35 - score * 0.2), label


def _semantic_risk_from_caption(caption: str, context_text: str | None) -> float:
    if not caption or not context_text:
        return 0.22

    caption_tokens = {token for token in _tokenize(caption) if len(token) > 2}
    context_tokens = {token for token in _tokenize(context_text) if len(token) > 2}
    if not caption_tokens or not context_tokens:
        return 0.2

    overlap = len(caption_tokens & context_tokens) / max(len(caption_tokens), 1)
    return float(np.clip(0.75 - overlap, 0.05, 0.85))


def _tokenize(text: str) -> list[str]:
    cleaned = "".join(char.lower() if char.isalnum() else " " for char in text)
    return [part for part in cleaned.split() if part]
