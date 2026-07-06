# signup-lab-k3s

Event-driven signup counter running on a single-node k3s cluster.
API accepts signups → Kafka → Worker persists to Postgres.

## Prerequisites

- Fresh Ubuntu (min 2GB RAM) droplet (DigitalOcean or similar)
- Non-root user with sudo:
```bash
adduser --disabled-password --gecos "" worker
echo "worker:YOUR_PASSWORD" | chpasswd
usermod -aG sudo worker
su - worker
```

## 1. Bootstrap

```bash
mkdir code && cd code
git clone https://github.com/echernenko/signup-lab-k3s.git
cd signup-lab-k3s
chmod +x bootstrap.sh deploy.sh
./bootstrap.sh
```

What it does:
1. Installs Docker CE from the official apt repo (skips if already present)
2. Adds your user to the `docker` group
3. Installs k3s via the official install script (skips if already present)
4. Prints Docker version and k3s node status to confirm both are ready

## 2. Deploy

```bash
exit          # refresh docker group membership
su - worker
cd code/signup-lab-k3s
./deploy.sh
```

What it does:
1. Builds two Docker images locally:
   - `signup-lab-api:latest` from `./api`
   - `signup-lab-worker:latest` from `./worker`
2. Imports them into the k3s containerd image store (`docker save | k3s ctr images import`) — no registry needed
3. Applies all manifests from `k8s/` — this creates Postgres, Kafka, API, and Worker deployments plus their services
4. Prints pod status

After deploy finishes, four pods should be running:
```
api, worker, kafka, postgres
```

## 3. Test

```bash
curl localhost:30800/signup?country=ua
curl localhost:30801/aggregation
```

API is exposed on NodePort **30800**, Worker on **30801**.

## Troubleshooting

```bash
sudo k3s kubectl get pods              # pod status
sudo k3s kubectl logs deploy/api -f    # api logs
sudo k3s kubectl logs deploy/worker -f # worker logs
sudo k3s kubectl logs deploy/kafka -f  # kafka logs
```

Redeploy after code changes:
```bash
./deploy.sh
sudo k3s kubectl rollout restart deploy/api deploy/worker
```
