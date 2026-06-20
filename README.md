# GridSense – Advanced Data Management Final Assessment

## Overview

GridSense is a multi-database smart-grid management platform developed for the Advanced Data Management course.

The system demonstrates the use of multiple database technologies, each selected for a specific workload:

* **PostgreSQL** – customer billing and invoices
* **MongoDB** – equipment catalog and asset metadata
* **Cassandra** – high-volume smart sensor telemetry
* **Neo4j** – electrical grid topology and network traversal
* **Redis** – alert caching and dashboard acceleration
* **FastAPI** – unified REST API layer

The entire platform is deployed using Docker Compose and exposed through a single API.

---

## Architecture

| Component         | Technology     | Purpose                                  |
| ----------------- | -------------- | ---------------------------------------- |
| Billing Database  | PostgreSQL     | Customer accounts, tariffs, invoices     |
| Equipment Catalog | MongoDB        | Asset metadata and equipment records     |
| Telemetry Store   | Cassandra      | High-volume time-series sensor readings  |
| Grid Topology     | Neo4j          | Network relationships and fault analysis |
| Cache & Alerts    | Redis          | Active alerts and dashboard caching      |
| API Layer         | FastAPI        | Unified REST interface                   |
| Deployment        | Docker Compose | Container orchestration                  |

---

## Project Structure

```text
gridsense/
│
├── api/
│   ├── db/
│   ├── models/
│   ├── routers/
│   └── main.py
│
├── postgres/
│   └── init.sql
│
├── mongo/
│
├── cql/
│   └── init.cql
│
├── neo4j/
│   └── import/
│       └── seed.cypher
│
├── scripts/
│   └── seed.py
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## Environment Configuration

Create a `.env` file using `.env.example`.

Example:

```env
POSTGRES_DB=gridsense_billing
POSTGRES_USER=gridsense_user
POSTGRES_PASSWORD=gridsense_pass

MONGO_INITDB_ROOT_USERNAME=gridsense_admin
MONGO_INITDB_ROOT_PASSWORD=gridsense_pass
MONGO_DB=gridsense_catalog

NEO4J_USER=neo4j
NEO4J_PASSWORD=gridsense_pass

REDIS_PASSWORD=gridsense_pass

CASSANDRA_KEYSPACE=gridsense
```

No credentials are stored in source code.

---

## Running the System

### Build and Start

```bash

gridsense/docker compose up --build
```

Run in background:

```bash
docker compose up -d --build
```

Stop:

```bash
docker compose down
```

---

## API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

OpenAPI JSON:

```text
http://localhost:8000/openapi.json
```

---

# Database Initialization

## PostgreSQL

Schema file:

```text
postgres/init.sql
```

Creates:

* customers
* tariffs
* billing_accounts
* invoices
* payments

---

## Cassandra

Initialization script:

```text
cql/init.cql
```

Creates:

* sensor_readings_by_sensor
* sensor_readings_by_minute

---

## Neo4j

Topology seed file:

```text
neo4j/import/seed.cypher
```

Creates:

* Substations
* Transformers
* SmartMeters
* FEEDS relationships
* SUPPLIES relationships

---

# Data Seeding

The project includes a complete multi-database seeding script.

Run:

```bash
python3 scripts/seed.py
```

The script is idempotent and can be executed multiple times without creating duplicate seed records.

---

## Seeded PostgreSQL Data

* 100 consumer accounts
* Billing accounts
* Tariff data
* Invoice records

---

## Seeded MongoDB Data

* 30 equipment records
* Transformer documents
* Smart meter documents
* Switchgear documents

Each equipment type uses a different document structure.

---

## Seeded Neo4j Data

* 10 substations
* 40 transformers
* 200 smart meters
* Grid relationships

---

## Seeded Cassandra Data

* 20 sensor IDs
* 50,000 sensor readings
* Voltage measurements
* Current measurements
* Power factor measurements
* Temperature measurements

---

# REST API Endpoints

## Billing

```text
GET    /billing/customers
POST   /billing/customers

GET    /billing/accounts

GET    /billing/invoices
POST   /billing/invoices

GET    /billing/account/{premise_id}
POST   /billing/invoice
```

---

## Equipment Catalog

```text
GET    /equipment
GET    /equipment/{asset_id}

POST   /equipment
PATCH  /equipment/{asset_id}
```

---

## Sensor Telemetry

```text
POST   /sensors/readings

GET    /sensors/{sensor_id}/readings
GET    /sensors/{sensor_id}/summary

GET    /sensors/dashboard/latest
```

---

## Grid Topology

```text
GET    /grid/nodes

POST   /grid/nodes
POST   /grid/relationships

GET    /grid/fault-impact/{node_id}
GET    /grid/restore-paths/{node_id}
GET    /grid/upstream/{node_id}
```

---

## Alerts

```text
GET    /alerts/active
POST   /alerts/publish
```

---

# Example Workflow

1. Start the platform using Docker Compose.
2. Seed all databases:

```bash
python3 scripts/seed.py
```

3. Open Swagger:

```text
http://localhost:8000/docs
```

4. Explore and test the REST endpoints.
5. Verify database contents through PostgreSQL, MongoDB, Cassandra, Neo4j, and Redis.

---

# Technologies Used

* Python 3
* FastAPI
* PostgreSQL 15
* MongoDB 7
* Cassandra 4
* Neo4j 5
* Redis 7
* Docker
* Docker Compose

---

# Author

Konstantinos Georgiou

Advanced Data Management – University of Thessaly
