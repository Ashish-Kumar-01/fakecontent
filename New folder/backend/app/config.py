from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


def _flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    api_title: str = "Fake Content Detection Assistant API"
    api_version: str = "2.0.0"
    enable_transformers_models: bool = _flag("FCDA_ENABLE_TRANSFORMERS", False)
    hf_image_model: str | None = os.getenv("FCDA_HF_IMAGE_MODEL")
    hf_multimodal_model: str | None = os.getenv("FCDA_HF_MULTIMODAL_MODEL")
    local_model_endpoint: str | None = os.getenv("FCDA_LOCAL_MODEL_ENDPOINT")
    local_model_timeout_seconds: float = float(os.getenv("FCDA_LOCAL_MODEL_TIMEOUT_SECONDS", "20"))


settings = Settings()
