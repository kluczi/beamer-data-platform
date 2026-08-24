import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE_PROJECT_DIR = PROJECT_ROOT / "dbt" / "reports"


def build_evidence_sources() -> None:
    subprocess.run(
        ["npm", "run", "sources:strict"],
        cwd=EVIDENCE_PROJECT_DIR,
        check=True,
    )
