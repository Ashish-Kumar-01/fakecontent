from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def analyze_video_temporal(video_path: Path) -> tuple[float, str, dict]:
    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        return 0.5, "Video could not be decoded reliably.", {"decode_failed": True}

    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    samples: list[np.ndarray] = []

    target_samples = 8
    indexes = []
    if frame_count > 0:
        indexes = sorted(set(int(i * max(frame_count - 1, 1) / max(target_samples - 1, 1)) for i in range(target_samples)))

    for index in indexes:
        capture.set(cv2.CAP_PROP_POS_FRAMES, index)
        ok, frame = capture.read()
        if ok and frame is not None:
            samples.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    capture.release()

    if len(samples) < 2:
        return 0.35, "Not enough frames were available for temporal analysis.", {
            "frame_count": frame_count,
            "fps": round(fps, 2),
            "sampled_frames": len(samples),
        }

    diffs = []
    brightness = []
    for idx, sample in enumerate(samples):
        brightness.append(float(sample.mean()) / 255.0)
        if idx > 0:
            prev = samples[idx - 1].astype(np.float32)
            curr = sample.astype(np.float32)
            diffs.append(float(np.mean(np.abs(curr - prev))) / 255.0)

    temporal_variance = float(np.std(diffs)) if diffs else 0.0
    brightness_variance = float(np.std(brightness))

    suspicious = 0.0
    reasons: list[str] = []
    if temporal_variance > 0.09:
        suspicious += 0.28
        reasons.append("unstable frame-to-frame changes")
    if brightness_variance > 0.14:
        suspicious += 0.2
        reasons.append("brightness flicker")
    if fps and fps < 12:
        suspicious += 0.1
        reasons.append("low frame rate source")

    score = _clamp(suspicious)
    summary = "Temporal video checks look stable."
    if reasons:
        summary = "Temporal video checks flagged " + ", ".join(reasons) + "."

    return score, summary, {
        "frame_count": frame_count,
        "fps": round(fps, 2),
        "sampled_frames": len(samples),
        "temporal_variance": round(temporal_variance, 4),
        "brightness_variance": round(brightness_variance, 4),
    }
