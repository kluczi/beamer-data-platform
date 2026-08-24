# Airflow

The local Airflow runtime starts with the Apple Container stack. DAG files in
[`dags/`](dags/) are mounted at `/opt/airflow/dags`.

The `beamer_pipeline` DAG runs marketplace ingestion and currency loading in
parallel, followed by dbt transformations and an Evidence source refresh. The
custom image contains the dependencies and project code used by all four tasks.

Build the image independently with:

```sh
./scripts/build-airflow
```

Airflow's built-in examples are disabled, and newly discovered DAGs are paused
by default.

Open the UI at <http://localhost:8080> and sign in with the
`AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` values from the project
`.env` file. This setup is only for local development.
