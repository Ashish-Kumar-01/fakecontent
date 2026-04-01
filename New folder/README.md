# Fake Content Detection Assistant

Local end-to-end MVP for detecting suspicious or manipulated media from a browser extension.

This project includes:

- a Chrome-compatible browser extension
- a Python backend API
- a multi-provider analysis pipeline for images and videos
- explainable scoring and evidence output

## What This MVP Does

The backend combines several lightweight analyzer families:

- forensic image checks
- temporal video checks
- provenance hashing against previously analyzed media
- context-risk analysis from nearby page text
- optional transformer-backed classifier and multimodal captioning providers
- optional external forensic model endpoint provider

This is still a risk assistant, not a truth engine. It produces a risk score with evidence, provider metadata, and confidence.

The default experience works locally with lightweight heuristics. You can now also enable stronger model integrations through either Hugging Face `transformers` models or your own external forensic model service.

## Run Backend

1. Create a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

For the Hugging Face local-model path, Python `3.11` or `3.12` is recommended. Python `3.13` can work for the lightweight backend, but some ML packages may not have stable wheels yet.

2. Install dependencies:

```powershell
pip install -r backend\requirements.txt
```

3. Optional: install ML extras for transformer-backed models:

```powershell
pip install -r backend\requirements-ml.txt
```

4. Optional: copy the env template and set model providers:

```powershell
Copy-Item backend\.env.example backend\.env
```

Suggested variables:

- `FCDA_ENABLE_TRANSFORMERS=true`
- `FCDA_HF_IMAGE_MODEL=Adieee5/deepfake-detection-ViT-CrossTraining`
- `FCDA_HF_MULTIMODAL_MODEL=nlpconnect/vit-gpt2-image-captioning`
- `FCDA_LOCAL_MODEL_ENDPOINT=http://127.0.0.1:9000/analyze`

5. Start the API from the `backend` folder:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or on Windows:

```powershell
.\start.ps1
```

The API health endpoint will be at `http://127.0.0.1:8000/health`.

## Load Extension

1. Open `chrome://extensions`
2. Enable `Developer mode`
3. Click `Load unpacked`
4. Select the `extension` folder

## Use It

1. Visit a page with an image or video
2. Hover over the media
3. Click `Analyze Media`
4. Wait for the report panel

The extension sends the media URL plus nearby page context to the backend and shows a richer evidence dashboard with:

- authenticity score
- manipulation risk
- top signals
- provider pipeline
- per-analyzer evidence cards

## Quick Test

After the backend starts, open:

```text
http://127.0.0.1:8000/health
```

You should see:

```json
{"status":"ok"}
```

## API Endpoints

- `GET /health`
- `GET /providers`
- `POST /analyze/url`
- `POST /analyze/upload`
- `GET /history`

## Notes

- Some websites block direct media fetching. In those cases, the extension may fail unless the media URL is publicly accessible.
- The provenance check compares against previously analyzed items stored locally in `backend/data/history.json`.
- Video analysis samples frames rather than processing the entire clip for speed.
- The transformer provider is generic by design. You should point it at models that are actually trained for synthetic media or forensic detection.
- The external model endpoint should return a JSON payload with an `evidence` array containing `analyzer`, `score`, `summary`, and optional `family` and `details`.
- The included default Hugging Face path is tuned for image analysis first. Video analysis still relies on sampled-frame heuristics unless you later add a stronger external video model service.

## Stronger Model Swap-In Ideas

You can now upgrade the backend without touching the extension UI:

- `transformers` image classifier for deepfake or edited-image classification
- `transformers` multimodal caption model for context mismatch checks
- local HTTP service wrapping a stronger model stack such as face-swap detection, artifact detection, or multimodal reasoning

The fusion layer will automatically include those extra signals in the final verdict.
