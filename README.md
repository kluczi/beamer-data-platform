# Beamer Data Platform

## Run with Apple Container

This project can run without Docker Desktop using Apple's `container` CLI on an
Apple-silicon Mac running macOS 26 or newer. The existing Dockerfile remains
valid because Apple Container builds and runs OCI images; only Compose has been
replaced with the two scripts below.

1. Install Apple Container from the [official release page](https://github.com/apple/container/releases).
2. Keep the project's `.env` file populated with the PostgreSQL, MinIO, and
   ClickHouse credentials.
3. Start the stack:

   ```sh
   ./scripts/container-up
   ```

4. Watch the one-shot scraper pipeline:

   ```sh
   container logs --follow beamer-scraper
   ```

Service ports remain available only on localhost: PostgreSQL `5432`, MinIO API
`9000`, MinIO Console `9001`, ClickHouse HTTP `8123`, ClickHouse native
`9002`, and CH-UI `3488`.

Open [CH-UI](http://localhost:3488) to browse and query ClickHouse. On first
use, sign in with the `CLICKHOUSE_USER` and `CLICKHOUSE_PASSWORD` values from
`.env`. Its workspace state is persisted in the `beamer-ch-ui-data` volume.

The scraper first writes immutable offer observations to DuckLake in MinIO. It
then loads every DuckLake scrape run not yet recorded in ClickHouse into
`beamer_warehouse.raw_offers_observations`, which is the table to use
from CH-UI.

## dbt transformations

dbt models live in `dbt/` and run in a local container against the
ClickHouse warehouse. After starting the stack, validate the connection and
build the models with:

```sh
./scripts/dbt debug
./scripts/dbt build
```

The starter mart, `beamer_warehouse.fct_offers_latest`, keeps the most
recent observation for each offer. Use `./scripts/dbt test` to run source and
model tests.

To stop the stack while retaining all database/object-store data:

```sh
./scripts/container-down
```

Data lives in Apple Container volumes named `beamer-postgres-data`,
`beamer-minio-data`, and `beamer-clickhouse-data`. The down script deliberately
does not remove them.

## Compose-style workflow

`container-compose` is installed on this Mac. It provides limited Compose
orchestration over Apple's `container` CLI; use the Apple-specific file rather
than `docker-compose.yml`:

```sh
container-compose --file compose.apple.yml up --build --detach
container logs --follow beamer-scraper
container-compose --file compose.apple.yml down
```

The adapter creates the network and volumes and waits for the declared
dependencies. Register the project DNS domain once before the first run:

```sh
sudo container system dns create beamer
```

The Apple Compose file uses the resulting generated service names, such as
`postgres.beamer` and `minio.beamer`, for reliable inter-container
connectivity.
