import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_source_schema_is_documented():
    text = (ROOT / "data" / "Review-Data-Pipeline.md").read_text(encoding="utf-8")
    for name in ["reviews_0-250.csv", "reviews_250-500.csv", "reviews_500-750.csv", "reviews_750-1250.csv", "reviews_1250-end.csv"]:
        assert name in text


def test_quality_report_has_expected_dataset_counts():
    report = json.loads((ROOT / "data" / "processed" / "review_pipeline_quality_report.json").read_text())
    assert report["raw_review_rows"] == 1094411
    assert report["unique_products_in_reviews"] == 2351
    assert report["products_in_catalog"] == 8494
    assert report["review_products_missing_from_catalog"] == 0
