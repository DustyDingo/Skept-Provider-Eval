# Skept Provider Eval

Throwaway service for comparing deepfake detection API providers before integrating into the Skept prototype (DustyDingo/Skept-prototype).

## Purpose
Run a social media clip URL through multiple detection API providers in parallel, log raw scores, and surface results in a simple review UI.

## Stack
FastAPI + uvicorn, yt-dlp ingestion, SQLite job logging, vanilla JS UI.

## Providers
- Resemble AI (DETECT-3B Omni) — audio + video
- Aurigin AI — audio only
- Sightengine — synthetic generation
- Reality Defender — audio + video

## Environment variables (set in Railway Variables tab)
RESEMBLE_API_KEY
AURIGIN_API_KEY
SIGHTENGINE_API_USER
SIGHTENGINE_API_SECRET
REALITY_DEFENDER_API_KEY

## Key files
main.py — FastAPI app and routes
ingestion/downloader.py — yt-dlp URL to temp file
providers/base.py — ProviderResult dataclass and abstract base
providers/*.py — one module per provider
jobs/runner.py — asyncio.gather() across all providers
jobs/store.py — SQLite read/write (eval/eval.db)
ui/static/index.html — review UI

## API routes
POST /analyse — body: {"url": "..."} — runs job, returns job_id + results
GET /jobs — all jobs with results
GET /jobs/{job_id} — single job detail
POST /jobs/{job_id}/ground_truth — body: {"label": "fake"|"authentic"|"unknown"}
GET /export — download all jobs as CSV

## Deploy
Railway auto-deploys from GitHub push.
Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT
