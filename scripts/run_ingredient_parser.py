from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ingredients.pipeline import parse_product_ingredients
from ingredients.quality import build_quality_report, suspicious_records

INPUT = ROOT / "data" / "raw" / "product_info.csv"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

products = pd.read_csv(INPUT, low_memory=False, usecols=["product_id", "ingredients"])
source_products = int(products["product_id"].nunique())
ingredient_products = int(products["ingredients"].notna().sum())

records, errors = parse_product_ingredients(INPUT)

records.to_csv(OUT / "product_ingredients.csv", index=False)
errors.to_csv(OUT / "ingredient_parse_errors.csv", index=False)

suspicious = suspicious_records(records)
suspicious.to_csv(OUT / "ingredient_parse_suspicious.csv", index=False)

report = build_quality_report(records, errors, ingredient_products)
report["source_catalog_products"] = source_products
report["products_without_ingredient_data"] = source_products - ingredient_products
report["products_with_ingredient_data_but_no_parsed_records"] = ingredient_products - int(records["product_id"].nunique())
report["suspicious_records"] = int(len(suspicious))
report["section_counts"] = records["section"].value_counts().head(50).to_dict() if not records.empty else {}
report["presence_counts"] = records["presence_type"].value_counts().to_dict() if not records.empty else {}

(OUT / "ingredient_parser_quality_report.json").write_text(
    json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(json.dumps(report, indent=2, ensure_ascii=False))
