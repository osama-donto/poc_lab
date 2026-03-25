# CLAUDE.md — Temporal POC on Local Kubernetes

This repo is a local Temporal workflow orchestration POC running  via Colima + k3d.
See `SPEC.md` for the full implementation task list.

## Project overview

Two-namespace Kubernetes setup:
- `temporal-system` — Temporal server (SQLite backend) + UI
- `temporal-workers` — Python worker pods that poll the task queue

Workers connect to the Temporal frontend via gRPC (port 7233). No ingress; use port-forward for local access.

## Environment

- Colima profile `k8s-temporal` must be running before any kubectl/docker commands
- k3d cluster name: `temporal-dev` (1 server, 3 agents)
- `KUBECONFIG=$(pwd)/.kube/config` — set by direnv, never touch the global kubeconfig
- Python 3.14 for worker code and scripts

Verify cluster access:
```
kubectl cluster-info
```

## Build & deploy

### Build and load the worker image
```bash
docker build -t python-temporal-worker:local ./worker/
k3d image import python-temporal-worker:local -c temporal-dev
```

### Deploy (order matters)
```bash
kubectl apply -f manifests/temporal-system/server.yaml
kubectl rollout status deployment/temporal-server -n temporal-system
kubectl apply -f manifests/temporal-workers/worker.yaml
```

### Run the demo workflow
```bash
./scripts/run_demo.sh
```

### Scale workers
```bash
./scripts/scale.sh up    # 5 replicas
./scripts/scale.sh down  # 1 replica
./scripts/scale.sh zero  # 0 replicas
```

### Access the UI
```bash
kubectl port-forward svc/temporal-ui 8233:8233 -n temporal-system
open http://localhost:8233
```

## Architecture

```
[scripts/start_workflow.py]
        │ gRPC :7233 (port-forwarded)
        ▼
[temporal-frontend svc] ──► [temporalio/auto-setup pod]
                                  │ SQLite /data/temporal.db (PVC)
[temporal-ui svc :8233] ──► [temporalio/ui pod]

[temporal-worker pods] ──► poll temporal-frontend:7233 outbound
   DataPipelineWorkflow
   activities: fetch_data → process_data → store_result
```

Worker image: `python-temporal-worker:local` (loaded into k3d, not pushed to a registry).

## Key files

| Path | Purpose |
|---|---|
| `manifests/temporal-system/server.yaml` | Temporal server + UI deployments and services |
| `manifests/temporal-workers/worker.yaml` | Worker deployment + HPA |
| `worker/` | Python worker image source |
| `scripts/start_workflow.py` | Trigger a workflow run from outside the cluster |
| `scripts/run_demo.sh` | Port-forward + run + teardown |
| `scripts/scale.sh` | Scale worker replicas |

## Constraints

- No Helm, no Cassandra, no Elasticsearch, no Prometheus, based on only lean engineering principles
- No changes to `$(pwd)/.kube/config` or `~/.zshrc`
- All `kubectl` commands rely on `KUBECONFIG` set by direnv (no `--kubeconfig` flag needed if direnv is active)
- No docker-compose, no local Temporal server binary
- Worker code is Python only
- Keep every file under 80 lines — split if needed
- If a step fails, surface the exact command that failed and stop; do not silently retry
