from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_review_source_schema_is_documented():
    text = (ROOT / "data" / "Review-Data-Pipeline.md").read_text(
        encoding="utf-8"
    )

    for name in [
        "reviews_0-250.csv",
        "reviews_250-500.csv",
        "reviews_500-750.csv",
        "reviews_750-1250.csv",
        "reviews_1250-end.csv",
    ]:
        assert name in text