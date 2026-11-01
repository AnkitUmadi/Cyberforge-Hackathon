import os
import sys
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

STAGES = {
    "200k": {
        "name": "Stage 1: Baseline Telemetry Profile (100 MB)",
        "source_db": ROOT / "out" / "killchain_safe_200k.duckdb"
    },
    "baseline": {
        "name": "Stage 1: Baseline Telemetry Profile (100 MB)",
        "source_db": ROOT / "out" / "killchain_safe_200k.duckdb"
    },
    "6gb": {
        "name": "Stage 2: Enterprise Multi-Subnet Dataset (6.5 GB)",
        "source_db": ROOT / "out" / "killchain_6gb.duckdb"
    },
    "6g": {
        "name": "Stage 2: Enterprise Multi-Subnet Dataset (6.5 GB)",
        "source_db": ROOT / "out" / "killchain_6gb.duckdb"
    },
    "30gb": {
        "name": "Stage 3: Mega Enterprise Campaign (30 GB Dataset)",
        "source_db": ROOT / "out" / "killchain_30gb.duckdb"
    },
    "30g": {
        "name": "Stage 3: Mega Enterprise Campaign (30 GB Dataset)",
        "source_db": ROOT / "out" / "killchain_30gb.duckdb"
    }
}

def switch(stage_key: str):
    stage_key = stage_key.lower().strip()
    if stage_key not in STAGES:
        print(f"Unknown stage: '{stage_key}'. Available stages: 200k, 6gb, 30gb")
        sys.exit(1)

    cfg = STAGES[stage_key]
    target_db = ROOT / "out" / "killchain.duckdb"
    src_db = cfg["source_db"]

    if not src_db.exists():
        print(f"Error: Source database {src_db} does not exist.")
        sys.exit(1)

    print("=" * 75)
    print(f"  SWITCHING ACTIVE DATASET: {cfg['name']}")
    print("=" * 75)

    # 1. Instant snapshot copy
    t0 = time.time()
    shutil.copyfile(src_db, target_db)
    print(f"[-] Database switched to {cfg['name']} ({time.time() - t0:.2f}s)")

    # 2. Regenerate HTML report with new dataset
    from src.killchain.report.generator import generate_report
    generate_report(db_path=str(target_db))

    # 3. Print evaluation metrics
    from src.killchain.eval.metrics import evaluate_engine
    evaluate_engine(db_path=str(target_db))

    print(f"\n[DONE] Refresh http://localhost:8000/ to see the live updated graph and metrics!\n")

if __name__ == "__main__":
    choice = sys.argv[1] if len(sys.argv) > 1 else "6gb"
    switch(choice)
