"""
External Dataset Builder Link
Project: Demand-Decision-Intelligence

Invokes scripts/build_external_datasets.py for dataset/external data collection.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import main functions from scripts/build_external_datasets.py
from scripts.build_external_datasets import (
    collect_calendar_data,
    collect_weather_data,
    collect_commodity_data,
    generate_reports
)

if __name__ == "__main__":
    print("Executing External Signal Enrichment Pipeline...")
    collect_calendar_data()
    collect_weather_data()
    collect_commodity_data()
    generate_reports()
    print("External Signal Enrichment Complete.")
