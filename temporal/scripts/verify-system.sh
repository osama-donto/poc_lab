#!/usr/bin/env bash
set -euo pipefail

POD=$(kubectl get pod -n temporal-system -l app=temporal-server \
  -o jsonpath='{.items[0].metadata.name}')

echo "=== Pods in temporal-system ==="
kubectl get pods -n temporal-system

ADDR=temporal-frontend.temporal-system.svc.cluster.local:7233

echo ""
echo "=== Cluster health ==="
kubectl exec -n temporal-system "$POD" -c temporal -- \
  temporal operator cluster health --address "$ADDR"

echo ""
echo "=== Default namespace ==="
kubectl exec -n temporal-system "$POD" -c temporal -- \
  temporal operator namespace describe default --address "$ADDR"

echo ""
echo "=== Services in temporal-system ==="
kubectl get svc -n temporal-system

echo ""
echo "All checks passed."
