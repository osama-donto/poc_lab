#!/usr/bin/env bash
# End-to-end demo: port-forward → scale → trigger workflow → teardown.
set -euo pipefail

NAMESPACE=temporal-workers
DEPLOYMENT=temporal-worker
PF_PID=""

cleanup() {
  echo ""
  echo "Cleaning up..."
  [[ -n "$PF_PID" ]] && kill "$PF_PID" 2>/dev/null || true
  echo "Port-forward stopped."
}
trap cleanup EXIT

# 1. Port-forward Temporal frontend gRPC
echo "Starting port-forward for Temporal frontend (7233)..."
kubectl port-forward svc/temporal-frontend 7233:7233 -n temporal-system &
PF_PID=$!
sleep 2  # allow port-forward to establish

# 2. Scale workers to 3
echo "Scaling workers to 3 replicas..."
kubectl scale deployment/$DEPLOYMENT -n $NAMESPACE --replicas=3
kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE

# 3. Trigger workflow
echo "Triggering DataPipelineWorkflow..."
python "$(dirname "$0")/start_workflow.py"

# 4. Scale back down
echo "Scaling workers back to 1..."
kubectl scale deployment/$DEPLOYMENT -n $NAMESPACE --replicas=1
echo "Demo complete."
