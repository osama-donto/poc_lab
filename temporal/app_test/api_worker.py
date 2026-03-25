"""Worker entry-point — polls the data-analysis task queue.

Registers DataAnalysisWorkflow and the three API activities.
Activities make outbound HTTP calls to the FastAPI service (API_SERVICE_URL).
"""
import asyncio, logging, os
from temporalio.client import Client
from temporalio.worker import Worker
from api_activities import get_dataset_summary, get_top_suppliers, llm_analyze
from api_workflow import DataAnalysisWorkflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE    = os.environ.get("TEMPORAL_TASK_QUEUE", "data-analysis")


async def main() -> None:
    client = await Client.connect(TEMPORAL_HOST)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[DataAnalysisWorkflow],
        activities=[get_dataset_summary, get_top_suppliers, llm_analyze],
        max_concurrent_activities=8,
    )
    logging.info("API worker ready — host=%s  queue=%s", TEMPORAL_HOST, TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
