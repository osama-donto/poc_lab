#!/usr/bin/env bash
# Scale temporal-worker deployment.
# Usage: scale.sh up|down|zero
set -euo pipefail

DEPLOYMENT=temporal-worker
NAMESPACE=temporal-workers

case "${1:-}" in
  up)
    REPLICAS=5
    ;;
  down)
    REPLICAS=1
    ;;
  zero)
    REPLICAS=0
    ;;
  *)
    echo "Usage: $0 up|down|zero" >&2
    exit 1
    ;;
esac

echo "Scaling $DEPLOYMENT to $REPLICAS replica(s)..."
kubectl scale deployment/$DEPLOYMENT -n $NAMESPACE --replicas=$REPLICAS

if [[ $REPLICAS -gt 0 ]]; then
  kubectl rollout status deployment/$DEPLOYMENT -n $NAMESPACE
  echo "Done — $REPLICAS replica(s) ready."
else
  echo "Done — scaled to zero."
fi
