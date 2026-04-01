from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .models import AnalysisResponse, AnalyzeUrlRequest
from .service import PROVENANCE, PROVIDERS, analyze_bytes, fetch_media


app = FastAPI(title=settings.api_title, version=settings.api_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": settings.api_version}


@app.get("/providers")
def providers() -> dict[str, list[str]]:
    return {"providers": [provider.name for provider in PROVIDERS]}


@app.get("/history")
def history() -> list[dict]:
    return PROVENANCE.history()


@app.post("/analyze/url", response_model=AnalysisResponse)
def analyze_url(payload: AnalyzeUrlRequest) -> AnalysisResponse:
    try:
        media_bytes = fetch_media(str(payload.media_url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return analyze_bytes(
            media_bytes=media_bytes,
            media_type=payload.media_type,
            source="url",
            page_url=payload.page_url,
            context_text=payload.context_text,
            media_url=str(payload.media_url),
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc


@app.post("/analyze/upload", response_model=AnalysisResponse)
async def analyze_upload(
    media_type: str = Form(...),
    page_url: str | None = Form(None),
    context_text: str | None = Form(None),
    file: UploadFile = File(...),
) -> AnalysisResponse:
    media_bytes = await file.read()
    try:
        return analyze_bytes(
            media_bytes=media_bytes,
            media_type=media_type,
            source="upload",
            page_url=page_url,
            context_text=context_text,
            media_url=file.filename,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}") from exc
