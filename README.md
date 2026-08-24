# Beamer Data Platform

Beamer is a local data engineering platform that collects vehicle marketplace
observations, preserves their history, transforms them in ClickHouse, and
publishes analytics-ready datasets and dashboards.

## Runtime

The supported local runtime is Apple Container on Apple silicon with macOS 26
or newer. Project scripts use Apple's `container` CLI directly. Docker Desktop
is not required and is not used by the documented workflow.

The repository retains `docker-compose.yml` as a compatibility definition, but
the actively tested setup is `scripts/container-up` with Apple Containers.

## Architecture

```text
                         Airflow
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
Marketplace ingestion   NBP exchange rates   dbt build
          |                 |                  |
          v                 v                  v
       DuckLake        ClickHouse raw     ClickHouse marts
       /      \                \               |
PostgreSQL   MinIO              +--------------+
 catalog     data files                        |
                                                v
                                         Evidence sources
```

The storage and transformation layers have distinct responsibilities:

- PostgreSQL stores DuckLake catalog and snapshot metadata.
- MinIO stores the DuckLake data files.
- ClickHouse is the analytical warehouse for raw observations, staging models,
  dimensions, facts, aggregates, and reporting marts.
- dbt defines transformations and data-quality tests.
- Evidence reads the reporting marts used by the dashboard.
- Airflow schedules and monitors the end-to-end dependency graph.

Each ingestion run receives a UUID `scrape_run_id`. Observations are appended to
DuckLake so historical price and mileage states remain available. Before a run
is copied into ClickHouse, the loader checks the `warehouse_loads` table, making
the warehouse load idempotent per run.

## Airflow pipeline

The `beamer_pipeline` DAG contains four tasks:

```text
ingest_source_data ---------+
                            +--> transform_warehouse --> refresh_evidence_sources
update_currency_rates ------+
```

- `ingest_source_data` discovers configured vehicle listings and loads new
  observations through DuckLake into ClickHouse.
- `update_currency_rates` loads current NBP currency rates.
- `transform_warehouse` runs `dbt build`, including configured data tests.
- `refresh_evidence_sources` refreshes the Evidence source cache after dbt
  completes successfully.

Task code is imported from the Python service modules. The Airflow image also
contains the Python ingestion dependencies, dbt Core, the ClickHouse adapter,
Node.js, and the Evidence dependencies required by those tasks.

Airflow and the host Evidence development server share
`dbt/reports/.evidence`. A successful source-refresh task therefore updates the
cache served at `localhost:3005`; reload the browser page to display the new
warehouse results.

## Repository layout

```text
dbt/                              dbt project and Evidence reporting project
orchestration/airflow/            Airflow image and DAG definitions
services/scraper/                 Marketplace ingestion and warehouse loading
services/dbt/                     Python entry point for dbt builds
services/evidence/                Python entry point for Evidence refreshes
scripts/container-up              Build and start the Apple Container stack
scripts/container-down            Stop the stack while retaining volumes
scripts/build-airflow             Build the complete local Airflow image
scripts/scraper                   Run marketplace ingestion independently
scripts/dbt                       Run dbt independently
compose.apple.yml                 Optional container-compose definition
docker-compose.yml                Compatibility definition, not primary runtime
```

## Configuration

Create `.env` in the repository root. It is intentionally ignored by Git
because it contains credentials and access tokens.

| Area | Variables |
| --- | --- |
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| MinIO | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET` |
| ClickHouse | `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, optionally `CLICKHOUSE_DB` |
| Marketplace | `GRAPHQL_URL`, `REFERER_URL`, `SITECODE`, `SCRAPE_TARGETS` |
| Access protection | optionally `DATADOME_CLIENT_ID`, `DATADOME_COOKIE` |
| Alerts | `DISCORD_WEBHOOK_URL` |
| Airflow | `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD` |

`SCRAPE_TARGETS` controls the vehicle filters. Multiple targets use a
comma-separated `make:model` format:

```env
SCRAPE_TARGETS=porsche:911,mercedes-benz:gle
```

`REFERER_URL` is an HTTP request header; it does not select which vehicles are
loaded.

## Start the platform

Install Apple Container from the
[official releases](https://github.com/apple/container/releases), populate
`.env`, and run:

```sh
./scripts/container-up
```

This builds the project images and starts PostgreSQL, MinIO, ClickHouse, CH-UI,
the ingestion runtime, and Airflow on the `beamer` Apple Container network.

Local endpoints:

| Service | Address |
| --- | --- |
| Airflow | [http://localhost:8080](http://localhost:8080) |
| CH-UI | [http://localhost:3488](http://localhost:3488) |
| PostgreSQL | `localhost:5432` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | [http://localhost:9001](http://localhost:9001) |
| ClickHouse HTTP | `http://localhost:8123` |
| ClickHouse native | `localhost:9002` |

Airflow credentials come from `AIRFLOW_ADMIN_USERNAME` and
`AIRFLOW_ADMIN_PASSWORD` in `.env`.

## Independent development commands

Run ingestion with every target configured in `.env`:

```sh
./scripts/scraper
```

Run a single configured target through the same ingestion code:

```sh
./scripts/scraper porsche:911 porsche-911
./scripts/scraper mercedes-benz:gle mercedes-gle
```

Build and test dbt models:

```sh
./scripts/dbt debug
./scripts/dbt build
```

Refresh and serve Evidence during dashboard development:

```sh
npm --prefix dbt/reports run sources:strict
npm --prefix dbt/reports run dev -- --host 127.0.0.1 --port 3005
```

Open [http://localhost:3005](http://localhost:3005) after the development
server starts.

## Stop the platform

```sh
./scripts/container-down
```

Project containers and the network are removed. PostgreSQL, MinIO, ClickHouse,
CH-UI, and Airflow data remain in Apple Container named volumes.

## Optional container-compose workflow

If `container-compose` is installed, the Apple-specific compose definition can
start the same services:

```sh
sudo container system dns create beamer
container-compose --file compose.apple.yml up --build --detach
container-compose --file compose.apple.yml down
```

The direct scripts remain the supported workflow because they handle Apple
Container names, networking, image builds, readiness checks, and persistent
volumes explicitly.
