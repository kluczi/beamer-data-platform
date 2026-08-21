# Beamer Data Platform

Beamer is a local data platform for collecting vehicle marketplace offers,
retaining their history, and building analytics-ready ClickHouse models. A
Python scraper discovers listings, stores each observed offer state in
DuckLake, and copies previously unloaded scrape runs into ClickHouse. dbt builds
the reporting layer, which will be served in Evidence. Airflow DAGs will
orchestrate the end-to-end pipeline.

## Architecture

```text
                       Airflow DAGs (planned)
                  orchestrate the full pipeline
                               |
                               v
Marketplace API -> Python ingestion -> DuckLake -> ClickHouse raw
                                          |              |
                              +-----------+              v
                              |                 dbt transformations
                              v                          |
                   +----------+----------+               v
                   |                     |       staging models
                   v                     v               |
             PostgreSQL                MinIO             v
             catalog metadata          data files   dimensions/facts
                                                         |
                                                         v
                                                    aggregations
                                                         |
                                                         v
                                                       marts
                                                         |
                                                         v
                                                 Evidence (planned)
```

The storage layers have separate responsibilities:

- PostgreSQL is the DuckLake catalog. It holds table and snapshot metadata,
  rather than the offer data queried by analysts.
- MinIO holds the DuckLake data files under the configured bucket.
- ClickHouse is the serving warehouse. The scraper creates and fills the raw
  tables, while dbt creates staging views and analytics tables.

Airflow and the ClickHouse-to-Evidence connection are planned orchestration and
presentation layers. Evidence itself is installed in `dbt/reports`, but it is
not connected to the warehouse yet.

Each scraper invocation uses a UUID `scrape_run_id`. The DuckLake table is
append-only at the application level, so repeated observations retain price and
mileage history. Before copying a run to ClickHouse, the loader checks
`warehouse_loads`; this makes warehouse loading idempotent per scrape run.

### Pipeline flow

1. The scraper calls the configured marketplace GraphQL endpoint to discover
   offer URLs.
2. It fetches each offer page and maps its `__NEXT_DATA__` payload to an offer
   observation.
3. Observations are appended in batches to
   `beamer_lake.raw.offers_observations`. PostgreSQL tracks the DuckLake catalog
   and MinIO stores its data files.
4. Any scrape run absent from ClickHouse's `warehouse_loads` table is copied to
   `beamer_warehouse.raw_offers_observations`.
5. dbt transforms the raw table through staging, dimensions and facts,
   aggregations, and final marts.
6. Evidence reads the marts to publish analytics pages and dashboards.

Airflow DAGs will schedule and monitor these steps as a single dependency
graph.

### dbt model graph

```text
raw_offers_observations (ClickHouse source)
└── stg_raw__offers_observations
    ├── dim__offers
    │   ├── agg__offers_by_brand
    │   └── agg__offers_by_fuel_type
    └── fct__offer_observations
        └── agg__daily_offer_observations
```

`dim__offers` contains the latest descriptive state for each offer and its
first/last observation timestamps. `fct__offer_observations` retains one row per
observed offer state. The aggregate models provide daily activity and current
inventory breakdowns. SQL keywords use lowercase consistently in both dbt
models and embedded application queries.

## Repository layout

```text
dbt/                     ClickHouse sources, staging models, marts, and tests
services/scraper/        Marketplace ingestion and DuckLake-to-ClickHouse load
scripts/container-up     Start the stack with Apple Container
scripts/container-down   Stop containers while retaining volumes
scripts/scraper          Run the one-shot scraper against the local services
scripts/dbt              Run dbt in a local container
compose.apple.yml        container-compose definition for Apple Container
docker-compose.yml       Docker Compose definition
```

## Configuration

Create a `.env` file in the repository root. The services expect these values:

| Area | Variables |
| --- | --- |
| PostgreSQL | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` |
| MinIO | `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`, `MINIO_BUCKET` |
| ClickHouse | `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`, optionally `CLICKHOUSE_DB` |
| Marketplace | `GRAPHQL_URL`, `REFERER_URL`, `SITECODE` |
| Access protection | optionally `DATADOME_CLIENT_ID`, `DATADOME_COOKIE` |
| Alerts | `DISCORD_WEBHOOK_URL` |

Do not commit `.env`; it contains credentials and access tokens.

## Run with Apple Container

The primary local workflow uses Apple's `container` CLI on an Apple-silicon Mac
running macOS 26 or newer.

1. Install Apple Container from the
   [official releases](https://github.com/apple/container/releases).
2. Populate `.env` with the configuration above.
3. Start the infrastructure and one-shot scraper:

   ```sh
   ./scripts/container-up
   ```

4. Follow the pipeline:

   ```sh
   container logs --follow beamer-scraper.beamer
   ```

To rerun the one-shot scraper in the foreground after the stack is running:

```sh
./scripts/scraper
```

The command rebuilds the local scraper image, replaces any previous scraper
container, and streams the run output directly to the terminal. Every scraper
execution sends a Discord alert when it succeeds or fails.

The services bind only to localhost:

| Service | Address |
| --- | --- |
| PostgreSQL | `localhost:5432` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |
| ClickHouse HTTP | `http://localhost:8123` |
| ClickHouse native | `localhost:9002` |

### Build and test dbt models

Once ClickHouse and the scraper have completed successfully, run:

```sh
./scripts/dbt debug
./scripts/dbt build
```

`dbt build` materializes the models and runs their configured tests. To run
only the tests, use `./scripts/dbt test`.

### Run Evidence locally

Evidence is installed in `dbt/reports` as a separate reporting project inside
the dbt directory. Build its template source and start the development server
with:

```sh
cd dbt
npm --prefix ./reports install
npm --prefix ./reports run sources
npm --prefix ./reports run dev -- --host 127.0.0.1 --port 3005
```

Open [http://127.0.0.1:3005](http://127.0.0.1:3005). Port 3005 avoids the
existing local service on port 3000. No ClickHouse connection is configured
yet.

### Stop the stack

```sh
./scripts/container-down
```

The command removes project containers and the network but retains data in the
`beamer-postgres-data`, `beamer-minio-data`, and `beamer-clickhouse-data`
volumes.

## Alternative orchestration

If `container-compose` is installed, use the Apple-specific Compose file:

```sh
sudo container system dns create beamer
container-compose --file compose.apple.yml up --build --detach
container logs --follow beamer-scraper.beamer
container-compose --file compose.apple.yml down
```

The DNS domain only needs to be registered once. The Compose file uses generated
service names such as `postgres.beamer`, `minio.beamer`, and
`clickhouse.beamer` for inter-container connectivity.

For a conventional Docker engine, `docker-compose.yml` describes the equivalent
development services and named volumes.
