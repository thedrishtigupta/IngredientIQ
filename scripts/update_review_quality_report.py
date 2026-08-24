import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

clean_path = ROOT / "data" / "processed" / "reviews_clean.csv"
report_path = ROOT / "data" / "processed" / "review_quality_report.json"

df = pd.read_csv(
    clean_path,
    usecols=["submission_time"]
)

dates = pd.to_datetime(df["submission_time"], errors="coerce")

with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

report["review_date_min"] = (
    dates.min().strftime("%Y-%m-%d")
    if dates.notna().any()
    else None
)

report["review_date_max"] = (
    dates.max().strftime("%Y-%m-%d")
    if dates.notna().any()
    else None
)

report["review_date_null_count"] = int(dates.isna().sum())
report["unique_review_dates"] = int(dates.nunique())

with open(report_path, "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("Updated review quality report:")
print("  min date:", report["review_date_min"])
print("  max date:", report["review_date_max"])
print("  null dates:", report["review_date_null_count"])
print("  unique dates:", report["unique_review_dates"])