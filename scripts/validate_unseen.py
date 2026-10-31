import os
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.killchain.db import get_connection, init_db
from src.killchain.ingest import ingest_file
from src.killchain.rules.runner import run_detection_rules
from src.killchain.correlate.engine import CorrelationEngine
from src.killchain.eval.metrics import evaluate_engine

VAL_LOG = r"C:\Users\Ankit Umadi\Documents\hack\data\sample_validation_100MB.log"
VAL_DB = r"out\validation.duckdb"
RULES_DIR = r"config\rules"

if os.path.exists(VAL_DB):
    try:
        os.remove(VAL_DB)
    except Exception:
        pass

print("===========================================================================")
print("  EMPIRICAL OUT-OF-SAMPLE VALIDATION TEST (Testing on Unseen 1 GB Offset)")
print("===========================================================================")

# 1. Ingest
t0 = time.time()
conn = get_connection(VAL_DB)
init_db(conn)
ingest_file(VAL_LOG, conn, file_idx=1)
ingest_time = time.time() - t0
print(f"\n[+] Unseen Sample Ingested in {ingest_time:.2f}s")

# 2. Run detection rules
t1 = time.time()
run_detection_rules(conn, RULES_DIR)
rules_time = time.time() - t1
print(f"\n[+] Rules Executed on Unseen Data in {rules_time:.2f}s")

# 3. Run correlation engine
t2 = time.time()
engine = CorrelationEngine(conn)
incidents = engine.correlate(min_stages=3)
correlate_time = time.time() - t2
print(f"\n[+] Correlation Engine Executed on Unseen Data in {correlate_time:.2f}s")
conn.close()

# 4. Run PRD Evaluation Metrics
print("\n" + "=" * 75)
print("  EVALUATING UNSEEN TEST SET METRICS")
print("=" * 75)
metrics = evaluate_engine(VAL_DB)
