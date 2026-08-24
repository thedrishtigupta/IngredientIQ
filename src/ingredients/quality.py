from __future__ import annotations

import re
from collections import Counter
from typing import Iterable

import pandas as pd


_METADATA_NAMES = re.compile(
    r"^(?:step\s*\d+|shade(?:\s*\d+)?|may\s+contain|\+/-|±|color|colour)\b",
    re.I,
)


def build_quality_report(records: pd.DataFrame, errors: pd.DataFrame, source_products: int) -> dict:
    if records.empty:
        return {
            "source_products": source_products,
            "parsed_products": 0,
            "ingredient_records": 0,
            "parse_error_products": len(errors),
            "empty_names": 0,
            "metadata_like_names": 0,
            "unbalanced_delimiters": 0,
            "duplicate_occurrences": 0,
            "primary_records": 0,
            "may_contain_records": 0,
            "unique_sections": 0,
            "ci_code_records": 0,
            "concentration_records": 0,
            "marker_records": 0,
        }

    names = records["ingredient_name"].fillna("").astype(str)
    metadata_like = names.str.match(_METADATA_NAMES, na=False)
    unbalanced = names.map(lambda x: any(x.count(a) != x.count(b) for a, b in [("(", ")"), ("[", "]"), ("{", "}")]))
    dup_cols = ["product_id", "position", "ingredient_raw", "presence_type", "section"]
    duplicates = int(records.duplicated(dup_cols, keep=False).sum())

    return {
        "source_products": int(source_products),
        "parsed_products": int(records["product_id"].nunique()),
        "ingredient_records": int(len(records)),
        "parse_error_products": int(len(errors)),
        "empty_names": int(names.str.strip().eq("").sum()),
        "metadata_like_names": int(metadata_like.sum()),
        "unbalanced_delimiters": int(unbalanced.sum()),
        "duplicate_occurrences": duplicates,
        "primary_records": int((records["presence_type"] == "PRIMARY").sum()),
        "may_contain_records": int((records["presence_type"] == "MAY_CONTAIN").sum()),
        "unique_sections": int(records["section"].nunique()),
        "ci_code_records": int(records["ci_codes"].map(bool).sum()),
        "concentration_records": int(records["concentration"].notna().sum()),
        "marker_records": int(records["markers"].map(bool).sum()),
    }


def suspicious_records(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return records.copy()
    names = records["ingredient_name"].fillna("").astype(str)
    mask = (
        names.str.strip().eq("")
        | names.str.match(_METADATA_NAMES, na=False)
        | names.str.contains(r"^(?:[+/-]|\(?\+/-\)?):?$", regex=True, na=False)
        | names.map(lambda x: any(x.count(a) != x.count(b) for a, b in [("(", ")"), ("[", "]"), ("{", "}")]))
    )
    return records.loc[mask].copy()
