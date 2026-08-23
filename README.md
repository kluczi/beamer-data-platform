# Beamer Data Platform

Beamer is a local data engineering platform for building and operating an
end-to-end analytical pipeline. It combines durable lake storage, a fast
analytical warehouse, tested SQL transformations, workflow orchestration, and
a lightweight business intelligence layer.

The repository demonstrates these data engineering patterns:

- append-only historical storage;
- separation of catalog metadata and physical data files;
- idempotent batch loading into a serving warehouse;
- dimensional and fact modeling with dbt;
- automated data quality tests;
- user-defined orchestration with Airflow;
- analytical dashboards backed by ClickHouse.

## Architecture

```text
                              Airflow
                        workflow orchestration
                                 |
                                 v
Source systems -> Python ingestion -> DuckLake -> ClickHouse raw
                                        |               |
                              +---------+               v
                              |                 dbt transformations
                              |                         |
                    +---------+---------+               v
                    |                   |         staging models
                    v                   v               |
              PostgreSQL             MinIO             v
              catalog metadata       data files   dimensions + facts
                                                        |
                                                        v
                                                   aggregations
                                                        |
                                                        v
                                                      marts
                                                        |
                                                        v
                                                    Evidence
```

### Component responsibilities

| Component | Responsibility |
| --- | --- |
| PostgreSQL | Stores the DuckLake catalog, snapshots, and table metadata |
| MinIO | Stores the physical DuckLake data files in S3-compatible object storage |
| DuckLake | Provides versioned lake storage and an analytical table abstraction |
| ClickHouse | Serves low-latency raw and modeled analytical data |
| dbt | Builds staging, dimensional, fact, aggregate, and reporting models |
| Airflow | Schedules and monitors user-defined data workflows |
| Evidence | Publishes analytical pages and dashboards from ClickHouse |
| CH-UI | Provides a local interface for inspecting ClickHouse |

## Data flow

1. A Python ingestion workload normalizes source records and assigns a unique
   run identifier.
2. Records are appended to DuckLake in batches. PostgreSQL maintains the
   catalog while MinIO stores the underlying data files.
3. Completed runs are loaded into ClickHouse. A warehouse load registry prevents
   the same run from being loaded more than once.
4. dbt transforms raw observations into reusable staging models, dimensions,
   facts, aggregates, and reporting marts.
5. dbt tests validate the configured source and model contracts.
6. Evidence queries the reporting layer to render the analytics dashboard.
7. Airflow can orchestrate these stages once project DAGs are added.

## dbt model graph

```text
raw_offers_observations
└── stg_raw__offers_observations
    ├── dim__offers
    │   ├── agg__offers_by_brand
    │   └── agg__offers_by_fuel_type
    └── fct__offer_observations
        └── agg__daily_offer_observations
```

The dimension stores the latest descriptive state of each entity. The fact
table retains historical observations, while aggregate and reporting models
support dashboard queries without repeating transformation logic in the BI
layer.

## Repository layout

```text
services/                 Data-producing and operational services
dbt/models/               ClickHouse sources, transformations, marts, and tests
dbt/reports/              Evidence reporting project
orchestration/airflow/    Airflow configuration and DAG directory
scripts/                  Local operational commands
compose.apple.yml         Compose definition for Apple Container
docker-compose.yml        Compose definition for Docker
```

## Configuration

Create a `.env` file in the repository root with the infrastructure
credentials required by the local services:

| Area | Variables |
| --- | --- |
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| MinIO | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET` |
| ClickHouse | `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, optionally `CLICKHOUSE_DB` |
| Airflow | `AIRFLOW_ADMIN_USERNAME`, `AIRFLOW_ADMIN_PASSWORD` |
| Alerts | optionally `DISCORD_WEBHOOK_URL` |

Do not commit `.env`; it contains local credentials and access tokens.

## Run locally with Apple Container

The primary development workflow uses Apple's `container` CLI on an
Apple-silicon Mac running macOS 26 or newer.

1. Install Apple Container from the
   [official releases](https://github.com/apple/container/releases).
2. Add the required values to `.env`.
3. Start the platform:

   ```sh
   ./scripts/container-up
   ```

The core services bind only to localhost:

| Service | Address |
| --- | --- |
| PostgreSQL | `localhost:5432` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |
| ClickHouse HTTP | `http://localhost:8123` |
| ClickHouse native | `localhost:9002` |
| CH-UI | `http://localhost:3488` |
| Airflow | `http://localhost:8080` |

### Run dbt

After raw data is available in ClickHouse, validate the connection and build
the transformation graph:

```sh
./scripts/dbt debug
./scripts/dbt build
```

`dbt build` materializes the selected models and runs their configured tests.
Run only the tests with:

```sh
./scripts/dbt test
```

### Use Airflow

Airflow runs in local standalone mode. Add your DAG files to
`orchestration/airflow/dags`; the directory is mounted directly at
`/opt/airflow/dags` and requires no image rebuild.

Open [http://localhost:8080](http://localhost:8080) and sign in with the
`AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` values from `.env`.

Built-in example DAGs are disabled, newly discovered DAGs begin paused, and
local task parallelism is limited to four. The standalone runtime is intended
only for local development.

### Run Evidence

Install the reporting dependencies, refresh the ClickHouse sources, and start
the development server:

```sh
cd dbt
npm --prefix ./reports install
npm --prefix ./reports run sources
npm --prefix ./reports run dev -- --host 127.0.0.1 --port 3005
```

Open [http://127.0.0.1:3005](http://127.0.0.1:3005).

### Stop the platform

```sh
./scripts/container-down
```

The command removes the project containers and network while retaining data in
the PostgreSQL, MinIO, ClickHouse, CH-UI, and Airflow named volumes.

## Compose alternatives

With `container-compose`, use the Apple-specific Compose definition:

```sh
sudo container system dns create beamer
container-compose --file compose.apple.yml up --build --detach
container-compose --file compose.apple.yml down
```

The DNS domain only needs to be registered once. Services use generated names
such as `postgres.beamer`, `minio.beamer`, and `clickhouse.beamer` for local
inter-container communication.

For a conventional Docker engine, `docker-compose.yml` provides the equivalent
development services and persistent volumes.
