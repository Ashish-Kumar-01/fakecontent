from __future__ import annotations

import re


HIGH_RISK_TERMS = {
    "breaking",
    "leaked",
    "exclusive",
    "shocking",
    "must watch",
    "viral",
    "share now",
    "forward this",
    "real footage",
    "unbelievable",
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def analyze_context_risk(context_text: str | None, page_url: str | None) -> tuple[float, str, dict]:
    text = (context_text or "").strip().lower()
    domain = ""
    if page_url:
        match = re.search(r"https?://([^/]+)", page_url.lower())
        if match:
            domain = match.group(1)

    matched_terms = sorted(term for term in HIGH_RISK_TERMS if term in text)
    suspicious = min(0.35, len(matched_terms) * 0.08)

    if any(domain.endswith(suffix) for suffix in ("blogspot.com", "wordpress.com", "telegram.me")):
        suspicious += 0.08

    score = _clamp(suspicious)
    summary = "Context signals look neutral."
    if matched_terms or score > 0.05:
        summary = "Context around the media includes virality or credibility risk signals."

    return score, summary, {
        "matched_terms": matched_terms,
        "domain": domain,
    }
