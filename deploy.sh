#!/usr/bin/env bash
set -euo pipefail

docker build -t signup-lab-api:latest ./api
docker build -t signup-lab-worker:latest ./worker

docker save signup-lab-api:latest | sudo k3s ctr images import -
docker save signup-lab-worker:latest | sudo k3s ctr images import -

sudo k3s kubectl apply -f k8s/
sudo k3s kubectl get pods
