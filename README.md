# GridSense – Distributed Smart Grid Data Platform

## Overview

GridSense is a distributed data management platform designed for monitoring and managing a smart electrical grid. The system integrates multiple database technologies, each selected according to its strengths and the characteristics of the data being managed.

The project demonstrates the use of relational, document, graph, time-series, and in-memory databases within a unified architecture exposed through a FastAPI application.

---

## Architecture

The platform consists of the following services:

| Service              | Technology | Purpose                                             |
| -------------------- | ---------- | --------------------------------------------------- |
| API Gateway          | FastAPI    | Unified REST API                                    |
| Billing Database     | PostgreSQL | Customer accounts, tariffs, invoices, and payments  |
| Equipment Catalog    | MongoDB    | Flexible equipment metadata and maintenance history |
| Time-Series Database | Cassandra  | High-volume sensor readings                         |
| Network Topology     | Neo4j      | Grid connectivity and fault propagation analysis    |
| Cache and Alerts     | Redis      | Dashboard caching and active fault alerts           |

---

## Database Design Decisions

### PostgreSQL

PostgreSQL is used for billing and customer management because the data is highly structured and requires strong consistency, transactions, and referential integrity.

Examples:

* Customers
* Billing accounts
* Tariffs
* Invoices
* Payments

### MongoDB

MongoDB stores equipment information because different equipment types have different attributes and metadata.

Examples:

* Transformers
* Smart meters
* Maintenance records
* Equipment specifications

### Cassandra

Cassandra is used for smart-grid sensor readings because it is designed for high write throughput and scalable time-series workloads.

Examples:

* Voltage measurements
* Current measurements
* Temperature readings
* Power factor readings

### Neo4j

Neo4j models the physical grid topology and enables graph traversal queries.

Examples:

* Substations
* Feeders
* Transformers
* Smart meters
* Fault impact analysis

### Redis

Redis is used for low-latency caching and temporary alert storage.

Examples:

* Dashboard summaries
* Active fault notifications
* Temporary operational data

---

## Project Structure

```text
gridsense/
├── api/
│   ├── db/
│   ├── models/
│   ├── routers/
│   └── main.py
├── postgres/
│   └── init.sql
├── mongo/
│   └── seed.js
├── cql/
│   └── init.cql
├── docker-compose.yml
├── Dockerfile
├── .env
├──README.md
├── scripts/
    └── seed.py
```

---

## Setup Instructions

### Prerequisites

* Docker
* Docker Compose
* Git

### Clone Repository

```bash
git clone <repository-url>
cd gridsense
```

### Start Services

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

---

## Example API Calls

### Retrieve Customers

```http
GET /billing/customers
```

### Retrieve Equipment Information

```http
GET /equipment/TX-1001
```

### Insert Sensor Reading

```http
POST /sensors/readings
```

Example payload:

```json
{
  "sensor_id": "S-1001",
  "district_id": "North",
  "ts": "2026-06-09T16:10:00",
  "voltage": 231.4,
  "current": 13.2,
  "power_factor": 0.98,
  "temperature": 42.5
}
```

### Fault Impact Analysis

```http
GET /grid/fault-impact/FDR-1
```

### Retrieve Cached Dashboard

```http
GET /cache/dashboard/North
```

---

## Demonstrated Features

* Multi-database architecture
* RESTful API design
* Docker container orchestration
* Time-series data storage
* Graph traversal queries
* Relational transaction processing
* Flexible document storage
* Distributed caching
* API documentation through Swagger

---
## Data Seeding

The project includes an automated multi-database seeding script:

```bash
python3 scripts/seed.py
```

The script populates all database systems with realistic sample data and is designed to be idempotent.

### Seeded Data

#### PostgreSQL

* 100 consumer accounts
* Billing accounts
* Sample invoice records
* Tariff information

#### MongoDB

* 30 equipment records
* 3 equipment types:

  * Transformers
  * Smart Meters
  * Switchgear
* Different document structures for each equipment type

#### Neo4j

* 10 substations
* 40 transformers
* 200 smart meters
* Grid connectivity relationships

#### Cassandra

* 20 sensor IDs
* 50,000 sensor readings
* Voltage, current, temperature and power-factor measurements

### Running the Seeder

Ensure all containers are running:

```bash
docker compose up -d
```

Then execute:

```bash
python3 scripts/seed.py
```

The script can be executed multiple times without creating duplicate records.

## Author

Konstantinos [Surname]

Advanced Data Management – Final Assignment

