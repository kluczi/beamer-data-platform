import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DBT_PROJECT_DIR = PROJECT_ROOT / "dbt"


def build_dbt() -> None:
    subprocess.run(
        [
            "dbt",
            "build",
            "--project-dir",
            str(DBT_PROJECT_DIR),
            "--profiles-dir",
            str(DBT_PROJECT_DIR),
        ],
        cwd=DBT_PROJECT_DIR,
        check=True,
    )
