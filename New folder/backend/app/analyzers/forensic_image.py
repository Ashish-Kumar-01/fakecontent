from __future__ import annotations

from io import BytesIO

import numpy as np
from PIL import Image, ImageChops, ImageFilter, ImageStat


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def analyze_image_forensics(media_bytes: bytes) -> tuple[float, str, dict]:
    image = Image.open(BytesIO(media_bytes)).convert("RGB")
    width, height = image.size
    grayscale = image.convert("L")
    arr = np.asarray(grayscale, dtype=np.float32)

    laplacian_energy = float(np.abs(np.diff(arr, axis=0)).mean() + np.abs(np.diff(arr, axis=1)).mean()) / 255.0
    extrema = grayscale.getextrema()
    dynamic_range = (extrema[1] - extrema[0]) / 255.0 if extrema else 0.0

    sharp = grayscale.filter(ImageFilter.SHARPEN)
    diff = ImageChops.difference(grayscale, sharp)
    noise_level = ImageStat.Stat(diff).mean[0] / 255.0

    suspicious = 0.0
    reasons: list[str] = []

    if dynamic_range < 0.18:
        suspicious += 0.24
        reasons.append("very low tonal range")
    if laplacian_energy < 0.03:
        suspicious += 0.22
        reasons.append("overly smooth edges")
    if noise_level > 0.16:
        suspicious += 0.18
        reasons.append("strong sharpening or compression noise")
    if width < 320 or height < 320:
        suspicious += 0.12
        reasons.append("low-resolution source")

    score = _clamp(suspicious)
    summary = "Image forensic checks did not find strong anomalies."
    if reasons:
        summary = "Image forensic checks flagged " + ", ".join(reasons) + "."

    details = {
        "width": width,
        "height": height,
        "dynamic_range": round(dynamic_range, 4),
        "edge_energy": round(laplacian_energy, 4),
        "noise_level": round(noise_level, 4),
    }
    return score, summary, details
