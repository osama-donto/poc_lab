"""DataPipelineWorkflow — runs vetcove and ezyvet pipelines in parallel."""
import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from activities import fetch_data, process_data, store_result

_OPTS = dict(
    schedule_to_close_timeout=timedelta(minutes=10),
    retry_policy=RetryPolicy(maximum_attempts=2),
)


@workflow.defn
class DataPipelineWorkflow:

    @workflow.run
    async def run(self, _: None = None) -> dict:
        workflow.logger.info("DataPipelineWorkflow: launching vetcove + ezyvet in parallel")
        vetcove, ezyvet = await asyncio.gather(
            self._pipeline("vetcove"),
            self._pipeline("ezyvet"),
        )
        workflow.logger.info("Both pipelines complete — vetcove=%s  ezyvet=%s", vetcove, ezyvet)
        return {"vetcove": vetcove, "ezyvet": ezyvet}

    async def _pipeline(self, source: str) -> str:
        """Three-step chain: fetch → process → store."""
        payload = await workflow.execute_activity(fetch_data,    source,  **_OPTS)
        payload = await workflow.execute_activity(process_data,  payload, **_OPTS)
        return  await workflow.execute_activity(store_result,   payload, **_OPTS)
