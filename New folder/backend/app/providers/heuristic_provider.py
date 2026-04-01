from __future__ import annotations

from ..analyzers import analyze_context_risk, analyze_image_forensics, analyze_video_temporal
from .base import AnalysisContext, AnalyzerProvider, ProviderResult


class HeuristicProvider(AnalyzerProvider):
    name = "heuristic"

    def analyze(self, context: AnalysisContext) -> list[ProviderResult]:
        results: list[ProviderResult] = []

        context_score, context_summary, context_details = analyze_context_risk(context.context_text, context.page_url)
        results.append(
            ProviderResult(
                analyzer="context_risk",
                score=context_score,
                summary=context_summary,
                details=context_details,
                family="context",
                provider=self.name,
            )
        )

        if context.media_type == "image":
            score, summary, details = analyze_image_forensics(context.media_bytes)
            results.append(
                ProviderResult(
                    analyzer="image_forensics",
                    score=score,
                    summary=summary,
                    details=details,
                    family="forensics",
                    provider=self.name,
                )
            )
        elif context.temp_video_path is not None:
            score, summary, details = analyze_video_temporal(context.temp_video_path)
            results.append(
                ProviderResult(
                    analyzer="temporal_video",
                    score=score,
                    summary=summary,
                    details=details,
                    family="temporal",
                    provider=self.name,
                )
            )

        return results
