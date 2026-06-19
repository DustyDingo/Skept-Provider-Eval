from __future__ import annotations

from datetime import datetime
from pathlib import Path

import aiosqlite

from providers.base import ProviderResult

DB_PATH = Path("eval/eval.db")

_CREATE_JOBS = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id      TEXT PRIMARY KEY,
    clip_url    TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    ground_truth TEXT NOT NULL DEFAULT 'unknown'
)
"""

_CREATE_RESULTS = """
CREATE TABLE IF NOT EXISTS results (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id           TEXT NOT NULL,
    provider         TEXT NOT NULL,
    modality         TEXT NOT NULL,
    raw_score        REAL,
    normalised_score REAL,
    label            TEXT,
    latency_ms       INTEGER,
    error            TEXT,
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
)
"""


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_JOBS)
        await db.execute(_CREATE_RESULTS)
        await db.commit()


async def save_job(job_id: str, clip_url: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO jobs (job_id, clip_url, created_at) VALUES (?, ?, ?)",
            (job_id, clip_url, datetime.utcnow().isoformat()),
        )
        await db.commit()


async def save_results(job_id: str, results: list[ProviderResult]) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """INSERT INTO results
               (job_id, provider, modality, raw_score, normalised_score, label, latency_ms, error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (job_id, r.provider, r.modality, r.raw_score,
                 r.normalised_score, r.label, r.latency_ms, r.error)
                for r in results
            ],
        )
        await db.commit()


async def get_all_jobs() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs ORDER BY created_at DESC") as cur:
            jobs = [dict(row) for row in await cur.fetchall()]
        for job in jobs:
            async with db.execute(
                "SELECT * FROM results WHERE job_id = ?", (job["job_id"],)
            ) as cur:
                job["results"] = [dict(row) for row in await cur.fetchall()]
    return jobs


async def get_job(job_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)) as cur:
            row = await cur.fetchone()
        if not row:
            return None
        job = dict(row)
        async with db.execute(
            "SELECT * FROM results WHERE job_id = ?", (job_id,)
        ) as cur:
            job["results"] = [dict(row) for row in await cur.fetchall()]
    return job


async def update_ground_truth(job_id: str, label: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE jobs SET ground_truth = ? WHERE job_id = ?",
            (label, job_id),
        )
        await db.commit()


async def export_all() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT j.job_id, j.clip_url, j.created_at, j.ground_truth,
                   r.provider, r.modality, r.raw_score, r.normalised_score,
                   r.label, r.latency_ms, r.error
            FROM jobs j
            LEFT JOIN results r ON j.job_id = r.job_id
            ORDER BY j.created_at DESC
        """) as cur:
            return [dict(row) for row in await cur.fetchall()]
