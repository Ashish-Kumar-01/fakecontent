from __future__ import annotations

import requests

from ..config import settings
from .base import AnalysisContext, AnalyzerProvider, ProviderResult


class LocalModelHTTPProvider(AnalyzerProvider):
    name = "local_http_model"

    def supports(self, context: AnalysisContext) -> bool:
        return bool(settings.local_model_endpoint)

    def analyze(self, context: AnalysisContext) -> list[ProviderResult]:
        response = requests.post(
            settings.local_model_endpoint,
            json={
                "media_type": context.media_type,
                "media_url": context.media_url,
                "page_url": context.page_url,
                "context_text": context.context_text,
                "media_hex": context.media_bytes.hex(),
            },
            timeout=settings.local_model_timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        results: list[ProviderResult] = []
        for item in payload.get("evidence", []):
            results.append(
                ProviderResult(
                    analyzer=item["analyzer"],
                    score=float(item["score"]),
                    summary=item["summary"],
                    details=item.get("details", {}),
                    family=item.get("family", "external"),
                    provider=self.name,
                )
            )
        return results
