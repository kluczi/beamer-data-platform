# Airflow

The local Airflow runtime starts with the rest of the platform. Add your DAG
files to [`dags/`](dags/); this directory is mounted at `/opt/airflow/dags` in
the Airflow container.

There are intentionally no example or project DAGs in this setup. Airflow's
built-in examples are disabled, and newly discovered DAGs are paused by default.

Open the UI at <http://localhost:8080> and sign in with the
`AIRFLOW_ADMIN_USERNAME` and `AIRFLOW_ADMIN_PASSWORD` values from the project
`.env` file. This setup is only for local development.
