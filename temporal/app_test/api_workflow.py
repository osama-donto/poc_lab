"""DataAnalysisWorkflow — parallel FastAPI calls + sequential LLM analysis.

Phase 1 (parallel via asyncio.gather):
  - dataset summary for vetcove + ezyvet
  - top-suppliers for vetcove + ezyvet

Phase 2 (sequential):
  - LLM analysis of combined results via OpenAI (proxied through FastAPI)
"""
import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from api_activities import get_dataset_summary, get_top_suppliers, llm_analyze

_OPTS = dict(
    schedule_to_close_timeout=timedelta(minutes=2),
    retry_policy=RetryPolicy(maximum_attempts=3),
)
_LLM_OPTS = dict(
    schedule_to_close_timeout=timedelta(minutes=5),
    retry_policy=RetryPolicy(maximum_attempts=2),
)


@workflow.defn
class DataAnalysisWorkflow:

    @workflow.run
    async def run(self, _: None = None) -> dict:
        workflow.logger.info("DataAnalysisWorkflow: launching 4 parallel FastAPI calls")

        # Phase 1 — parallel HTTP calls to FastAPI pandas endpoints
        v_summary, e_summary, v_suppliers, e_suppliers = await asyncio.gather(
            workflow.execute_activity(get_dataset_summary, "vetcove", **_OPTS),
            workflow.execute_activity(get_dataset_summary, "ezyvet",  **_OPTS),
            workflow.execute_activity(get_top_suppliers,   "vetcove", **_OPTS),
            workflow.execute_activity(get_top_suppliers,   "ezyvet",  **_OPTS),
        )
        workflow.logger.info("Phase 1 complete — all 4 activities returned")

        # Phase 2 — LLM analysis via FastAPI → OpenAI
        llm_result = await workflow.execute_activity(
            llm_analyze,
            {
                "prompt": (
                    "Compare these two veterinary supply datasets. "
                    "Highlight key differences in pricing, supplier diversity, and scale."
                ),
                "data": {
                    "vetcove_summary":   v_summary,
                    "ezyvet_summary":    e_summary,
                    "vetcove_suppliers": v_suppliers,
                    "ezyvet_suppliers":  e_suppliers,
                },
            },
            **_LLM_OPTS,
        )
        workflow.logger.info("Phase 2 complete — LLM analysis done")

        return {
            "vetcove_summary":   v_summary,
            "ezyvet_summary":    e_summary,
            "vetcove_suppliers": v_suppliers,
            "ezyvet_suppliers":  e_suppliers,
            "llm_analysis":      llm_result.get("analysis", ""),
        }
