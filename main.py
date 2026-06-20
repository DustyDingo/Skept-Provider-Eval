from __future__ import annotations

import csv
import io
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ingestion.downloader import cleanup, download
from jobs import runner, store


@asynccontextmanager
async def lifespan(app: FastAPI):
    await store.init_db()
    yield


app = FastAPI(title="Skept Provider Eval", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="ui/static"), name="static")

_INDEX = Path("ui/static/index.html")


class AnalyseRequest(BaseModel):
    url: str


class GroundTruthRequest(BaseModel):
    label: str


@app.get("/", response_class=HTMLResponse)
async def index():
    return _INDEX.read_text(encoding="utf-8")


@app.post("/analyse")
async def analyse(req: AnalyseRequest):
    job_id = uuid.uuid4().hex
    paths: dict | None = None
    try:
        paths = await download(req.url)
        results = await runner.run_all_providers(paths)
        await store.save_results(job_id, req.url, results)
        return {"job_id": job_id, "results": [r.__dict__ for r in results]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    finally:
        if paths:
            cleanup(paths)


@app.get("/jobs")
async def get_jobs():
    return await store.get_all_jobs()


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


@app.post("/jobs/{job_id}/ground_truth")
async def set_ground_truth(job_id: str, req: GroundTruthRequest):
    if req.label not in ("fake", "authentic", "unknown"):
        raise HTTPException(status_code=400, detail="label must be fake, authentic, or unknown")
    await store.update_ground_truth(job_id, req.label)
    return {"ok": True}


@app.get("/export")
async def export():
    rows = await store.export_all()
    if not rows:
        raise HTTPException(status_code=404, detail="no data to export")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=eval_export.csv"},
    )
