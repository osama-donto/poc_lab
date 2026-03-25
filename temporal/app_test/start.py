"""Trigger a DataPipelineWorkflow run from outside the cluster."""
import asyncio, os, sys
from temporalio.client import Client
from workflow import DataPipelineWorkflow

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE    = os.environ.get("TEMPORAL_TASK_QUEUE", "data-pipeline")
WORKFLOW_ID   = os.environ.get("WORKFLOW_ID", "data-pipeline-001")


async def main() -> None:
    client = await Client.connect(TEMPORAL_HOST)
    handle = await client.start_workflow(
        DataPipelineWorkflow.run,
        id=WORKFLOW_ID,
        task_queue=TASK_QUEUE,
    )
    print(f"Workflow started  id={handle.id}  run_id={handle.result_run_id}")
    result = await handle.result()
    print(f"Done: {result}")


if __name__ == "__main__":
    asyncio.run(main())
