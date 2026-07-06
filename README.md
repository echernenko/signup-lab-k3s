## Pre-work
NOTE: suggest to not push anything for a sandbox Ubuntu box to this repo. Either edit via browser or push from main laptop. 
Be sure you have keys set up for github and remote is set:
```
git remote set-url origin git@github.com:echernenko/signup-lab.git
```

## Actual Setup
1. Create a new DigitalOcean Droplet: https://cloud.digitalocean.com/droplets
2. Login to droplet and create a new user to not work under root:
```
adduser --disabled-password --gecos "" worker
echo "{USER}:{PASSWORD}" | chpasswd
usermod -aG sudo {USER}
su - {USER}
```
3. create a folder in /home/{USER}/ called `code`. Navigate to it.
4. Clone the repo in question: 
```
git clone git@github.com:echernenko/signup-lab.git
chmod +x bootstrap.sh && ./bootstrap.sh
exit
su - worker
cd /home/{USER}/code/signup-lab
docker compose up -d --build
```

## Test
```
curl "localhost:8000/signup?country=ua"
curl "localhost:8000/aggregation"
```

## Debugging
```
# see the process running
docker compose ps

# see logs
docker compose logs api
```
4x containers should be running
```
 ✔ Image postgres:16               Pulled                                                                                      9.4s
 ✔ Image signup-lab-worker         Built                                                                                      14.8s
 ✔ Image signup-lab-api            Built                                                                                      14.8s
 ✔ Network signup-lab_default      Created                                                                                     0.1s
 ✔ Volume signup-lab_pgdata        Created                                                                                     0.0s
 ✔ Container signup-lab-kafka-1    Started                                                                                     1.2s
 ✔ Container signup-lab-postgres-1 Started                                                                                     1.1s
 ✔ Container signup-lab-worker-1   Started                                                                                     2.8s
 ✔ Container signup-lab-api-1      Started
```
