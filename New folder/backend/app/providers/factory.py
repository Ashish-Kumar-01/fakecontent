from __future__ import annotations

from ..config import settings
from .base import AnalyzerProvider
from .heuristic_provider import HeuristicProvider
from .local_http_provider import LocalModelHTTPProvider


def build_provider_stack() -> list[AnalyzerProvider]:
    providers: list[AnalyzerProvider] = [HeuristicProvider()]

    if settings.local_model_endpoint:
        providers.append(LocalModelHTTPProvider())

    if settings.enable_transformers_models:
        from .transformers_provider import TransformersProvider

        providers.append(TransformersProvider())

    return providers
