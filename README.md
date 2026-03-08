# 🚕 NYC Taxi Graph Pipeline

An end-to-end streaming data pipeline that ingests NYC Yellow Taxi trip records, stores them as a graph in Neo4j, and runs graph analytics including **PageRank** and **Breadth-First Search (BFS)**.

The pipeline is built in two layers:
- **Local** — Dockerized Neo4j with the full dataset loaded and graph algorithms exposed via Python
- **Scalable** — Kubernetes-orchestrated streaming pipeline using Kafka, Zookeeper, and Kafka Connect to stream data in real time into Neo4j

---

## Architecture



| Component | Role |
|---|---|
| **Kafka** | Distributed message broker — ingests taxi trip records as a stream |
| **Zookeeper** | Coordinates and manages Kafka brokers |
| **Kafka Connect** | Consumes Kafka topic and writes data into Neo4j via the Neo4j Sink Connector |
| **Neo4j** | Graph database storing `Location` nodes and `TRIP` relationships |
| **GDS Plugin** | Runs PageRank and BFS graph algorithms directly in Neo4j |
| **Docker** | Local development — containerized Neo4j with dataset pre-loaded |
| **Minikube** | Local Kubernetes cluster orchestrating all components |

---

## Graph Schema

```
(:Location {name: int}) -[:TRIP {distance: float, fare: float, pickup_dt: datetime, dropoff_dt: datetime}]-> (:Location {name: int})
```

- **Nodes** — One `Location` node per unique pickup/dropoff zone (Bronx zones only, 42 total)
- **Relationships** — One `TRIP` relationship per taxi trip, filtered to `distance > 0.1` and `fare > $2.50`
- **Dataset** — NYC TLC Yellow Taxi Trip Records, March 2022

---

## Project Structure

```
nyc-taxi-graph-pipeline/
├── docker/
│   ├── Dockerfile             # Neo4j container with GDS plugin and data pre-loaded
│   └── data_loader.py         # Parquet ingestion + graph schema creation
├── kubernetes/
│   ├── zookeeper-setup.yaml   # Zookeeper Deployment + Service
│   ├── kafka-setup.yaml       # Kafka Deployment + Service
│   ├── neo4j-values.yaml      # Neo4j Helm values (enterprise + GDS)
│   └── kafka-neo4j-connector.yaml  # Kafka Connect Deployment
├── analytics/
│   └── interface.py           # PageRank and BFS via Neo4j GDS
├── .gitignore
└── README.md
```

---

## Part 1 — Local Docker Setup

### Prerequisites

- Docker

### Data

This project uses the NYC TLC Yellow Taxi Trip Records (March 2022).

Download the dataset before building:
```bash
wget -O docker/yellow_tripdata_2022-03.parquet \
  https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2022-03.parquet
```

> The Dockerfile also downloads it automatically during the build, so this step is optional if you are just building the image.

### Build & Run

```bash
# Build the image
docker build -t nyc-taxi-graph -f docker/Dockerfile docker/

# Run the container
docker run -d -p 7474:7474 -p 7687:7687 --name nyc-taxi nyc-taxi-graph
```

> ⏳ Wait **2–4 minutes** after starting — Neo4j takes time to initialize and load the dataset.

### Verify Data

Once running, open your browser at `http://localhost:7474` and connect with:
- **URL**: `neo4j://localhost:7687`
- **Username**: `neo4j`
- **Password**: `graphprocessing`

Try these queries:
```cypher
-- View schema
CALL db.schema.visualization();

-- View sample data
MATCH (n) RETURN n LIMIT 25;

-- Count nodes and relationships
MATCH (n) RETURN count(n) AS nodes;
MATCH ()-[r]->() RETURN count(r) AS relationships;
```

Expected: **42 nodes**, **1530 relationships**

---

## Part 2 — Graph Analytics

The `analytics/interface.py` module connects to Neo4j and exposes two graph algorithms.

### Setup

```bash
pip install neo4j
```

### Usage

```python
from analytics.interface import Interface

db = Interface("neo4j://localhost:7687", "neo4j", "graphprocessing")

# PageRank — returns [max_node, min_node]
result = db.pagerank(max_iterations=20, weight_property="distance")
print(result)
# [{'name': 132, 'score': 4.231}, {'name': 1, 'score': 0.150}]

# BFS — returns shortest path from start to end
path = db.bfs(start_node=159, last_node=212)
print(path)
# [{'path': [{'name': 159}, {'name': 212}]}]

db.close()
```

### PageRank

Uses the Neo4j GDS `gds.pageRank.stream` algorithm with:
- Damping factor: `0.85`
- Configurable `max_iterations`
- Configurable `weight_property` (`distance` or `fare`)
- Returns the nodes with the **highest** and **lowest** PageRank scores

### BFS (Breadth-First Search)

Finds the shortest traversal path between two `Location` nodes using `TRIP` relationships.

---

## Part 3 — Kubernetes Streaming Pipeline

### Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- [Helm](https://helm.sh/docs/intro/install/)

### Start Minikube

```bash
# Start with enough resources
minikube start --cpus=4 --memory=8192
```

### Deploy All Components

```bash
# 1. Zookeeper
kubectl apply -f kubernetes/zookeeper-setup.yaml

# 2. Kafka
kubectl apply -f kubernetes/kafka-setup.yaml

# 3. Neo4j via Helm
helm repo add neo4j https://helm.neo4j.com/neo4j
helm repo update
helm install my-neo4j-release neo4j/neo4j -f kubernetes/neo4j-values.yaml

# 4. Neo4j Service
kubectl apply -f kubernetes/neo4j-service.yaml

# 5. Kafka-Neo4j Connector
kubectl apply -f kubernetes/kafka-neo4j-connector.yaml
```

### Verify Pods

```bash
kubectl get pods
```

You should see all pods in `Running` state:
```
zookeeper-deployment-xxx    1/1   Running
kafka-deployment-xxx        1/1   Running
my-neo4j-release-0          1/1   Running
kafka-neo4j-connector-xxx   1/1   Running
```

### Expose Ports

In separate terminals:
```bash
# Kafka
kubectl port-forward svc/kafka-service 9092:9092

# Neo4j
kubectl port-forward svc/neo4j-service 7474:7474 7687:7687
```

### Stream Data

```bash
# Produce messages to the Kafka topic
python data_producer.py
```

Data flows: `Producer → Kafka (nyc_taxicab_data topic) → Kafka Connect → Neo4j`

---

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=flat&logo=neo4j&logoColor=white)
![Apache Kafka](https://img.shields.io/badge/Apache%20Kafka-231F20?style=flat&logo=apachekafka&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=flat&logo=kubernetes&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)
![Helm](https://img.shields.io/badge/Helm-0F1689?style=flat&logo=helm&logoColor=white)

- **Python** — Data loading, analytics interface
- **Neo4j 2025.08** — Graph database
- **Neo4j GDS 2.21.0** — Graph Data Science plugin (PageRank, BFS)
- **Apache Kafka 7.3.3** — Message streaming
- **Zookeeper 7.3.3** — Kafka coordination
- **Kafka Connect** — Neo4j Sink Connector
- **Docker** — Container for local Neo4j setup
- **Kubernetes / Minikube** — Container orchestration
- **Helm** — Kubernetes package management

---

## License

MIT