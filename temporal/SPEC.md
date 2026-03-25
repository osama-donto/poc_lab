# Temporal POC — Implementation Spec

This file contains the original task specification for building the Temporal orchestration POC.
See `CLAUDE.md` for how to work in this repo.

---

## Task 1 — Deploy Temporal (two-plane, PSQL, no Helm)

Create and apply two manifest files:

### manifests/temporal-system/server.yaml
- Namespace: temporal-system
- Single Deployment: temporalio/auto-setup:latest
  - db=postgreSQL
  - PVC 2Gi mounted at /data
  - resources: request 512Mi/200m, limit 1Gi/500m
  - replicas: 1 (fixed — never scale this)
- ClusterIP Service: temporal-frontend, port 7233
- Single Deployment: temporalio/ui:latest
  - TEMPORAL_ADDRESS=temporal-frontend.temporal-system.svc.cluster.local:7233
  - resources: request 128Mi/50m
- ClusterIP Service: temporal-ui, port 8233→8080

### manifests/temporal-workers/worker.yaml
- Namespace: temporal-workers
- Deployment: temporal-worker
  - image: python-temporal-worker:local (built from ./worker/Dockerfile)
  - env: TEMPORAL_HOST_PORT, TEMPORAL_NAMESPACE=default, TEMPORAL_TASK_QUEUE=demo-queue
  - resources: request 128Mi/100m, limit 512Mi/500m
  - replicas: 1 (will be scaled manually for demo)
  - NO Service — workers only poll outbound
- HPA: min=0 max=10 cpu=60%

Apply in order: temporal-system first, wait for rollout, then temporal-workers.

---

## Task 2 — Python worker image

Create ./worker/ with:

### worker/requirements.txt
temporalio==1.7.0   # pin this exact version

### worker/activities.py
Three activities that simulate real work with sleep():
- fetch_data(url: str) -> dict      # pretend HTTP call, sleep 1s
- process_data(data: dict) -> dict  # CPU work simulation, sleep 2s
- store_result(result: dict) -> str # DB write simulation, sleep 0.5s

### worker/workflows.py
One workflow DataPipelineWorkflow:
- execute() calls the three activities in sequence
- each activity uses activity.start_to_close_timeout=timedelta(seconds=30)
- workflow logs start/end of each step

### worker/main.py
- connect to TEMPORAL_HOST_PORT env var
- register DataPipelineWorkflow and all three activities
- run worker on TEMPORAL_TASK_QUEUE env var
- log worker start with host and queue name

### worker/Dockerfile
FROM python:3.14-slim
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
CMD ["python", "main.py"]

Build with: docker build -t python-temporal-worker:local ./worker/
Load into k3d: k3d image import python-temporal-worker:local -c temporal-dev

---

## Task 3 — Starter script (triggers a workflow from outside the cluster)

### scripts/start_workflow.py
- connect to localhost:7233 (port-forwarded)
- start DataPipelineWorkflow with workflow_id="demo-{timestamp}"
- print workflow ID and run ID
- poll and print result

### scripts/run_demo.sh
#!/bin/bash
# Port-forward in background, run workflow, then kill forward
kubectl port-forward svc/temporal-frontend 7233:7233 -n temporal-system &
PF_PID=$!
sleep 2
python scripts/start_workflow.py
kill $PF_PID

---

## Task 4 — Scale demo scripts

### scripts/scale.sh
#!/bin/bash
# Usage: ./scripts/scale.sh [up|down|zero]
case $1 in
  up)   kubectl scale deployment/temporal-worker --replicas=5 -n temporal-workers ;;
  down) kubectl scale deployment/temporal-worker --replicas=1 -n temporal-workers ;;
  zero) kubectl scale deployment/temporal-worker --replicas=0 -n temporal-workers ;;
esac
kubectl get pods -n temporal-workers -w

---

## Task 5 — Access

After apply:
  kubectl port-forward svc/temporal-ui 8233:8233 -n temporal-system
  open http://localhost:8233
