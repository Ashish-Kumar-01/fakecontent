from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class ProvenanceStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def _read(self) -> list[dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write(self, payload: list[dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def fingerprint(self, media_bytes: bytes) -> str:
        return hashlib.sha256(media_bytes).hexdigest()

    def analyze(self, media_bytes: bytes, media_url: str | None, media_type: str) -> tuple[float, str, dict[str, Any], str]:
        fingerprint = self.fingerprint(media_bytes)
        entries = self._read()
        match = next((item for item in entries if item["fingerprint"] == fingerprint), None)

        score = 0.0
        summary = "No prior identical media found in local provenance history."
        details: dict[str, Any] = {"known_before": False}

        if match:
            details = {
                "known_before": True,
                "first_seen_source": match.get("media_url"),
                "first_seen_type": match.get("media_type"),
            }
            if media_url and match.get("media_url") and match["media_url"] != media_url:
                score = 0.24
                summary = "This exact media was analyzed before from a different source URL."
            else:
                summary = "This exact media already exists in local provenance history."

        entries.append(
            {
                "fingerprint": fingerprint,
                "media_url": media_url,
                "media_type": media_type,
            }
        )
        self._write(entries[-500:])
        return score, summary, details, fingerprint

    def history(self) -> list[dict[str, Any]]:
        return self._read()
