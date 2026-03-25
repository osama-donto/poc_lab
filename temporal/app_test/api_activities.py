"""Temporal activities that call the FastAPI service via HTTP.

Each activity is a thin HTTP client — business logic lives in api_service.py.
API_SERVICE_URL env var selects the target (defaults to in-cluster DNS).
"""
import os
import httpx
from temporalio import activity

API_URL = os.environ.get(
    "API_SERVICE_URL",
    "http://api-service.temporal-workers.svc.cluster.local:8000",
)


@activity.defn
async def get_dataset_summary(source: str) -> dict:
    activity.logger.info("Fetching summary for dataset=%s", source)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_URL}/datasets/{source}/summary")
        resp.raise_for_status()
        data = resp.json()
    activity.logger.info("Summary for %s: %d rows", source, data.get("row_count", 0))
    return data


@activity.defn
async def get_top_suppliers(source: str) -> dict:
    activity.logger.info("Fetching top suppliers for dataset=%s", source)
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{API_URL}/datasets/{source}/top-suppliers")
        resp.raise_for_status()
        data = resp.json()
    activity.logger.info(
        "Top suppliers for %s: %d unique", source, data.get("total_unique_suppliers", 0)
    )
    return data


@activity.defn
async def llm_analyze(payload: dict) -> dict:
    activity.logger.info("Sending data to LLM for analysis (prompt=%s...)", payload.get("prompt", "")[:40])
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f"{API_URL}/llm/analyze", json=payload)
        resp.raise_for_status()
        data = resp.json()
    activity.logger.info("LLM analysis complete (%d chars)", len(data.get("analysis", "")))
    return data
