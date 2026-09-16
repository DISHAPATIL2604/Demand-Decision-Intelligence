"""
Forecasting Baseline Module
Demand-Decision-Intelligence

Provides simple strong baselines (Naive Lag-1, Seasonal Naive Lag-7, Rolling Mean 7)
and Ridge ML regression benchmark evaluated using chronological time splits.
"""

from pathlib import Path
import sys

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from forecasting.forecast_pipeline import (
    evaluate_predictions,
    feature_query,
    reports_dir,
    demand_file
)

def run_baseline_evaluation():
    """
    Executes the full forecasting pipeline and returns metrics.
    """
    import subprocess
    script_path = project_root / "forecasting" / "forecast_pipeline.py"
    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    return res.returncode

if __name__ == "__main__":
    sys.exit(run_baseline_evaluation())
