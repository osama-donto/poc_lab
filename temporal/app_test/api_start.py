"""Trigger a DataAnalysisWorkflow run from outside the cluster.

Usage:
  python api_start.py                        # auto-generated workflow ID
  python api_start.py my-workflow-id-001     # explicit workflow ID
"""
import asyncio, os, sys, time
from temporalio.client import Client
from api_workflow import DataAnalysisWorkflow

TEMPORAL_HOST = os.environ.get("TEMPORAL_HOST", "localhost:7233")
TASK_QUEUE    = os.environ.get("TEMPORAL_TASK_QUEUE", "data-analysis")


async def main() -> None:
    workflow_id = sys.argv[1] if len(sys.argv) > 1 else f"data-analysis-{int(time.time())}"
    client = await Client.connect(TEMPORAL_HOST)
    handle = await client.start_workflow(
        DataAnalysisWorkflow.run,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )
    print(f"Started  id={handle.id}  run_id={handle.result_run_id}")
    result = await handle.result()
    print("\n=== LLM Analysis ===")
    print(result.get("llm_analysis", "(none)"))
    print("\n=== Vetcove top suppliers ===")
    for row in result.get("vetcove_suppliers", {}).get("top_10", []):
        print(f"  {row['supplier']}: {row['count']}")
    print("\n=== ezyVet top suppliers ===")
    for row in result.get("ezyvet_suppliers", {}).get("top_10", []):
        print(f"  {row['supplier']}: {row['count']}")


if __name__ == "__main__":
    asyncio.run(main())
