from __future__ import annotations

from pathlib import Path

import pandas as pd

from .parser import parse_product_row


def parse_product_ingredients(input_csv: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse all non-empty product ingredient fields.

    Returns:
        records: one row per ingredient occurrence.
        errors: one row per product that could not be parsed.
    """
    products = pd.read_csv(input_csv, low_memory=False)
    required = {"product_id", "ingredients"}
    missing = required - set(products.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    records: list[dict] = []
    errors: list[dict] = []

    for row in products[["product_id", "ingredients"]].itertuples(index=False):
        product_id, raw = row
        if pd.isna(raw) or not str(raw).strip():
            continue
        try:
            parsed = parse_product_row({"product_id": product_id, "ingredients": raw})
            records.extend(r.as_dict() for r in parsed)
        except Exception as exc:  # keep the ETL running; report the bad row
            errors.append({
                "product_id": product_id,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            })

    return pd.DataFrame(records), pd.DataFrame(errors)
