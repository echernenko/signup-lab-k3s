# Signup Lab (k3s Cluster Edition)

This repository contains a simple, event-driven user signup processing system. It has been migrated from a Docker Compose setup to a lightweight **k3s** Kubernetes cluster to simulate production-like orchestration with minimal resource footprint.

---

## Architecture Overview

The system consists of the following components deployed within the k3s cluster:

1. **API Service**:
   - Built with FastAPI (`api/main.py`).
   - Ingests signup events (e.g., `/signup?country=ua`).
   - Produces events to the Kafka broker.
   - Exposed on the host node via port **`30800`** (using a NodePort service mapping to container port `8000`).

2. **Worker Service**:
   - Built with FastAPI (`worker/worker.py`).
   - Subscribes to the Kafka `signups` topic.
   - Persists events and tracks cumulative aggregates in a PostgreSQL database.
   - Serves aggregates via the `/aggregation` endpoint.
   - Exposed on the host node via port **`30801`** (using a NodePort service mapping to container port `8001`).

3. **Message Broker (Kafka)**:
   - A single-node Kafka deployment (`k8s/kafka.yaml`) serving as the message ingestion pipeline on port `9092`.

4. **Database (PostgreSQL)**:
   - Persistent relational storage for signup metrics (`k8s/postgres.yaml`).
   - Configured with a `PersistentVolumeClaim` (`pgdata`) requesting `1Gi` storage to ensure data persistence across container updates or pod restarts.

---

## Deployment & Bootstrap Scripts

We use two shell scripts to provision and deploy the application:

### 1. [bootstrap.sh](file:///Users/admin/code/signup-lab-k3s/bootstrap.sh)
Automates host preparation on a clean Ubuntu instance:
- Installs **Docker** (to build images locally).
- Adds the active user to the `docker` system group.
- Installs **k3s** Kubernetes distribution.

### 2. [deploy.sh](file:///Users/admin/code/signup-lab-k3s/deploy.sh)
Performs local container build and deployment inside the cluster without requiring an external container registry:
1. Builds local Docker images for the API (`signup-lab-api:latest`) and Worker (`signup-lab-worker:latest`).
2. Directly exports/saves these images and imports them into the k3s container runtime namespace (`k3s ctr images import`).
3. Applies all Kubernetes resource manifests under the [k8s/](file:///Users/admin/code/signup-lab-k3s/k8s) directory.
4. Outputs the status of the newly created pods.

---

## Step-by-Step Setup Guide

### Pre-work
To avoid committing directly from a remote sandbox environment, configure SSH keys for GitHub on the VM, or edit code locally.
Verify the origin remote:
```bash
git remote set-url origin git@github.com:echernenko/signup-lab.git
```

### Actual VM Provisioning & Setup
1. **Launch a Droplet**: Create a new Ubuntu Droplet on DigitalOcean.
2. **Configure a Non-Root User**: Log in as `root` and configure a dedicated `worker` user with sudo permissions:
   ```bash
   adduser --disabled-password --gecos "" worker
   echo "worker:PASSWORD" | chpasswd
   usermod -aG sudo worker
   su - worker
   ```
3. **Clone the Project**: Create a directory structure and pull the repository:
   ```bash
   mkdir -p ~/code && cd ~/code
   git clone git@github.com:echernenko/signup-lab.git
   cd signup-lab
   ```
4. **Bootstrap Docker & k3s**: Execute the installation script:
   ```bash
   chmod +x bootstrap.sh && ./bootstrap.sh
   ```
5. **Apply Group Changes (Critical)**:
   Since [bootstrap.sh](file:///Users/admin/code/signup-lab-k3s/bootstrap.sh) modifies docker group permissions, you must refresh your session:
   ```bash
   exit
   su - worker
   cd ~/code/signup-lab
   ```
6. **Deploy Applications**: Run the deployment script to build images and spin up resources:
   ```bash
   chmod +x deploy.sh && ./deploy.sh
   ```

---

## Verification & Testing

Since Kubernetes NodePorts are used, components are reached via their host-bound NodePorts (`30800` and `30801`), rather than docker-compose host port forwarding.

### 1. Ingest Event via API
Send a signup request (mapped to host port `30800`):
```bash
curl "http://localhost:30800/signup?country=ua"
```
*Response:*
```json
{"status":"queued","country":"ua","date":"2026-07-05"}
```

### 2. Verify Aggregation via Worker
Query the worker endpoint (mapped to host port `30801`) to see aggregates updated from Postgres:
```bash
curl "http://localhost:30801/aggregation"
```
*Response:*
```json
{"2026-07-05":1}
```

---

## Troubleshooting & Operations

Use `kubectl` commands via the wrapper `sudo k3s kubectl` to administer the cluster:

- **Check status of all resources**:
  ```bash
  sudo k3s kubectl get all -n default
  ```
- **Inspect Deployment Pods**:
  ```bash
  sudo k3s kubectl get pods
  ```
- **View Container Logs**:
  - API logs: `sudo k3s kubectl logs deployment/api -f`
  - Worker logs: `sudo k3s kubectl logs deployment/worker -f`
  - Postgres database logs: `sudo k3s kubectl logs deployment/postgres -f`
- **Inspect PVC Status**:
  ```bash
  sudo k3s kubectl get pvc
  ```
- **Execute queries directly on Postgres**:
  Connect using psql client inside the DB pod:
  ```bash
  sudo k3s kubectl exec -it deployment/postgres -- psql -U signup -d signups
  ```
- **Trigger a rollout/restart**:
  ```bash
  sudo k3s kubectl rollout restart deployment/api
  sudo k3s kubectl rollout restart deployment/worker
  ```
