"""Trigger a DataPipelineWorkflow run from outside the cluster."""
import asyncio, os, sys, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app_test"))

from temporalio.client import Client
from workflow import DataPipelineWorkflow

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE    = os.environ.get("TEMPORAL_TASK_QUEUE", "data-pipeline")


async def main() -> None:
    workflow_id = (
        sys.argv[1]
        if len(sys.argv) > 1
        else f"data-pipeline-{int(time.time())}"
    )
    client = await Client.connect(TEMPORAL_HOST)
    handle = await client.start_workflow(
        DataPipelineWorkflow.run,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    print(f"Started  id={handle.id}  run_id={handle.result_run_id}")
    result = await handle.result()
    print(f"Done: {result}")


if __name__ == "__main__":
    asyncio.run(main())
