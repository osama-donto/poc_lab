"""Worker entry-point — polls the data-pipeline task queue."""
import asyncio, logging, os
from temporalio.client import Client
from temporalio.worker import Worker
from activities import fetch_data, process_data, store_result
from workflow import DataPipelineWorkflow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
)

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE    = os.environ.get("TEMPORAL_TASK_QUEUE", "data-pipeline")


async def main() -> None:
    client = await Client.connect(TEMPORAL_HOST)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[DataPipelineWorkflow],
        activities=[fetch_data, process_data, store_result],
        max_concurrent_activities=6,
    )
    logging.info("Worker ready — host=%s  queue=%s", TEMPORAL_HOST, TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
