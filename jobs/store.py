from __future__ import annotations

from datetime import datetime
from pathlib import Path

import aiosqlite

from providers.base import ProviderResult

DB_PATH = Path("eval/eval.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS jobs (
    job_id           TEXT,
    clip_url         TEXT,
    provider         TEXT,
    modality         TEXT,
    raw_score        REAL,
    normalised_score REAL,
    label            TEXT,
    latency_ms       INTEGER,
    error            TEXT,
    ground_truth     TEXT NOT NULL DEFAULT 'unknown',
    created_at       TEXT
)
"""


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(_CREATE_TABLE)
        await db.commit()


async def save_results(job_id: str, clip_url: str, results: list[ProviderResult]) -> None:
    now = datetime.utcnow().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(
            """INSERT INTO jobs
               (job_id, clip_url, provider, modality, raw_score, normalised_score,
                label, latency_ms, error, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [
                (job_id, clip_url, r.provider, r.modality, r.raw_score,
                 r.normalised_score, r.label, r.latency_ms, r.error, now)
                for r in results
            ],
        )
        await db.commit()


async def get_all_jobs() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC, job_id"
        ) as cur:
            rows = [dict(row) for row in await cur.fetchall()]

    seen: dict[str, dict] = {}
    for row in rows:
        jid = row["job_id"]
        if jid not in seen:
            seen[jid] = {
                "job_id": jid,
                "clip_url": row["clip_url"],
                "created_at": row["created_at"],
                "ground_truth": row["ground_truth"],
                "results": [],
            }
        seen[jid]["results"].append({
            "provider": row["provider"],
            "modality": row["modality"],
            "raw_score": row["raw_score"],
            "normalised_score": row["normalised_score"],
            "label": row["label"],
            "latency_ms": row["latency_ms"],
            "error": row["error"],
        })
    return list(seen.values())


async def get_job(job_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jobs WHERE job_id = ?", (job_id,)
        ) as cur:
            rows = [dict(row) for row in await cur.fetchall()]

    if not rows:
        return None
    first = rows[0]
    return {
        "job_id": first["job_id"],
        "clip_url": first["clip_url"],
        "created_at": first["created_at"],
        "ground_truth": first["ground_truth"],
        "results": [
            {
                "provider": r["provider"],
                "modality": r["modality"],
                "raw_score": r["raw_score"],
                "normalised_score": r["normalised_score"],
                "label": r["label"],
                "latency_ms": r["latency_ms"],
                "error": r["error"],
            }
            for r in rows
        ],
    }


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
        async with db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC"
        ) as cur:
            return [dict(row) for row in await cur.fetchall()]
