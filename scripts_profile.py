from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ingredients.pipeline import parse_product_ingredients

input_csv = ROOT / "data" / "raw" / "product_info.csv"
records, errors = parse_product_ingredients(input_csv)
print(f"ingredient records: {len(records):,}")
print(f"parse errors: {len(errors):,}")
print(f"products parsed: {records.product_id.nunique():,}")
