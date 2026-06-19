# Skept Provider Eval

Throwaway service for comparing deepfake detection API providers before integrating into the Skept prototype (DustyDingo/Skept-prototype).

## Purpose
Run a social media clip URL through multiple detection API providers in parallel, log raw scores, and surface results in a simple review UI. Used to determine best provider(s) for audio deepfake, video deepfake, and synthetic generation detection.

## Stack
- FastAPI + uvicorn
- yt-dlp for ingestion (URL → temp file)
- SQLite for job logging (eval/eval.db)
- Vanilla JS single-page UI

## Providers
- Resemble AI (DETECT-3B Omni) — audio + video
- Aurigin AI — audio only
- Sightengine — synthetic generation (video frames)
- Reality Defender — audio + video

## Environment variables (set in Railway)
- RESEMBLE_API_KEY
- AURIGIN_API_KEY
- SIGHTENGINE_API_USER
- SIGHTENGINE_API_SECRET
- REALITY_DEFENDER_API_KEY

## Key files
- main.py — FastAPI app, routes
- ingestion/downloader.py — yt-dlp download to temp file
- providers/base.py — ProviderResult dataclass and abstract base
- providers/*.py — one file per provider
- jobs/runner.py — parallel execution via asyncio.gather()
- jobs/store.py — SQLite read/write
- ui/static/index.html — review UI

## API routes
POST /analyse  body: {"url": "..."} → triggers job, returns job_id + results
GET  /jobs     → list all jobs with results
GET  /jobs/{job_id} → single job detail
POST /jobs/{job_id}/ground_truth  body: {"label": "fake"|"authentic"|"unknown"}
GET  /export   → download all jobs as CSV

## Deploy
Railway auto-deploys from GitHub push. Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT
