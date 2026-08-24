from __future__ import annotations

import argparse
import ast
import json
import os
import sys
from pathlib import Path

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"


def pick(*paths):
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError("Could not find any of:\n" + "\n".join(map(str, paths)))


PRODUCTS = pick(RAW / "product_info.csv")
PRODUCT_INGREDIENTS = pick(
    PROCESSED / "product_ingredients.csv",
    ROOT / "data" / "product_ingredients.csv",
)
KNOWLEDGE = pick(PROCESSED / "ingredient_knowledge_v2.csv")
PROFILES = pick(PROCESSED / "product_functional_profile_v2.csv")
REVIEWS = pick(PROCESSED / "reviews_clean.csv")
REVIEW_SUMMARY = pick(PROCESSED / "product_review_summary.csv")


def nullable(value):
    return None if pd.isna(value) else value


def to_bool(value):
    if pd.isna(value):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "1.0", "true", "t", "yes", "y"}:
        return True
    if text in {"0", "0.0", "false", "f", "no", "n"}:
        return False
    raise ValueError(f"Cannot convert value to boolean: {value!r}")


def as_json_array(value):
    if pd.isna(value):
        return []
    if isinstance(value, list):
        return value
    text = str(value).strip()
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return [text]
    return parsed if isinstance(parsed, list) else [parsed]


def connect():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "ingredientiq"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )


def clear_database(conn):
    with conn.cursor() as cur:
        cur.execute("""
            TRUNCATE TABLE
                product_functional_profiles,
                product_review_summary,
                reviews,
                product_ingredients,
                ingredient_knowledge,
                ingredients,
                products
            RESTART IDENTITY CASCADE;
        """)
    conn.commit()


def load_products(conn):
    df = pd.read_csv(PRODUCTS, low_memory=False)
    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        rows.append((
            str(d["product_id"]), d["product_name"], d.get("brand_name"),
            d.get("primary_category"), d.get("secondary_category"),
            nullable(d.get("price_usd")), nullable(d.get("rating")),
            nullable(d.get("reviews")), nullable(d.get("loves_count")),
            d.get("ingredients"), nullable(d.get("brand_id")),
            d.get("variation_type"), d.get("variation_value"),
            d.get("variation_desc"), nullable(d.get("value_price_usd")),
            nullable(d.get("sale_price_usd")), to_bool(d.get("limited_edition")),
            to_bool(d.get("new")), to_bool(d.get("online_only")),
            to_bool(d.get("out_of_stock")), to_bool(d.get("sephora_exclusive")),
            json.dumps(as_json_array(d.get("highlights"))),
            d.get("tertiary_category"), nullable(d.get("child_count")),
            nullable(d.get("child_max_price")), nullable(d.get("child_min_price")),
        ))
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO products (
                product_id, product_name, brand, category, subcategory,
                price, rating, review_count, loves_count, raw_ingredients,
                brand_id, variation_type, variation_value, variation_desc,
                value_price_usd, sale_price_usd, limited_edition, is_new,
                online_only, out_of_stock, sephora_exclusive, highlights,
                tertiary_category, child_count, child_max_price, child_min_price
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                    %s,%s,%s,%s,%s,%s)
        """, rows)
    conn.commit()
    print(f"products: {len(rows):,}")


def load_ingredients(conn):
    df = pd.read_csv(PRODUCT_INGREDIENTS, usecols=["normalized_name"])
    names = sorted({
        str(x).strip() for x in df["normalized_name"].dropna()
        if str(x).strip()
    })
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO ingredients (canonical_name) VALUES (%s)",
            [(x,) for x in names],
        )
    conn.commit()
    print(f"ingredients: {len(names):,}")


def load_product_ingredients(conn):
    df = pd.read_csv(PRODUCT_INGREDIENTS, low_memory=False)
    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        normalized = str(d["normalized_name"]).strip()
        if not normalized:
            continue
        rows.append((
            str(d["product_id"]), normalized, int(d["position"]),
            d["presence_type"], d.get("section") or "main",
            nullable(d.get("concentration")), nullable(d.get("concentration_unit")),
            json.dumps(as_json_array(d.get("ci_codes"))),
            json.dumps(as_json_array(d.get("markers"))),
            d["ingredient_raw"],
        ))
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO product_ingredients (
                product_id, ingredient_id, position, presence_type, section,
                concentration, concentration_unit, ci_codes, markers, ingredient_raw
            )
            SELECT %s, i.ingredient_id, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s
            FROM (SELECT %s::text AS normalized_name) s
            JOIN ingredients i ON i.canonical_name = s.normalized_name
        """, [
            (pid, pos, presence, section, conc, unit, ci, markers, raw, name)
            for pid, name, pos, presence, section, conc, unit, ci, markers, raw in rows
        ])
    conn.commit()
    print(f"product_ingredients: {len(rows):,}")


def load_knowledge(conn):
    df = pd.read_csv(KNOWLEDGE, low_memory=False)
    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        conf = d.get("confidence")
        if pd.isna(conf):
            conf_value = None
        else:
            conf_value = {"HIGH": 1.0, "MEDIUM": 0.7, "LOW": 0.4}.get(str(conf).upper(), None)
        rows.append((
            str(d["canonical_name"]).strip(),
            json.dumps([x.strip() for x in str(d["functional_groups"]).split(";") if x.strip()]),
            json.dumps([x.strip() for x in str(d["user_goals"]).split(";") if x.strip()]),
            json.dumps([x.strip() for x in str(d["roles"]).split(";") if x.strip()]),
            str(d["fragrance_related"]).upper() == "YES",
            str(d["colorant_related"]).upper() == "YES",
            nullable(d.get("notes")), conf_value, nullable(d.get("source")),
            nullable(d.get("knowledge_status")),
        ))
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO ingredient_knowledge (
                ingredient_id, functional_groups, user_goals, roles,
                fragrance_related, colorant_related, notes, confidence,
                source, knowledge_status
            )
            SELECT i.ingredient_id, %s::jsonb, %s::jsonb, %s::jsonb,
                   %s,%s,%s,%s,%s,%s
            FROM ingredients i
            WHERE i.canonical_name = %s
        """, [
            (fg, goals, roles, fr, co, notes, conf, source, status, name)
            for name, fg, goals, roles, fr, co, notes, conf, source, status in rows
        ])
    conn.commit()
    print(f"ingredient_knowledge: {len(rows):,}")


def load_profiles(conn):
    df = pd.read_csv(PROFILES, low_memory=False)
    feature_cols = [c for c in df.columns if c != "product_id"]
    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        features = {}
        for c in feature_cols:
            v = d[c]
            if pd.notna(v):
                features[c] = int(v) if isinstance(v, float) and v.is_integer() else v
        rows.append((str(d["product_id"]), json.dumps(features), "ingredient_knowledge_v2"))
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO product_functional_profiles
                (product_id, features, knowledge_version)
            VALUES (%s,%s::jsonb,%s)
        """, rows)
    conn.commit()
    print(f"product_functional_profiles: {len(rows):,}")


def load_reviews(conn):
    columns = [
        "review_id", "author_id", "rating", "is_recommended", "helpfulness",
        "total_feedback_count", "total_neg_feedback_count",
        "total_pos_feedback_count", "submission_time", "review_text",
        "review_title", "skin_tone", "eye_color", "skin_type", "hair_color",
        "product_id", "product_name", "brand_name", "price_usd",
        "has_review_text", "has_review_title", "source_file"
    ]
    total = 0
    for chunk in pd.read_csv(REVIEWS, usecols=columns, chunksize=25_000, low_memory=False):
        rows = []
        for r in chunk.itertuples(index=False):
            d = r._asdict()
            rows.append((
                str(d["review_id"]), str(d["product_id"]), nullable(d["rating"]),
                nullable(d["review_title"]), nullable(d["review_text"]),
                to_bool(d["is_recommended"]), nullable(d["helpfulness"]),
                nullable(d["submission_time"]), nullable(d["author_id"]),
                nullable(d["total_feedback_count"]),
                nullable(d["total_neg_feedback_count"]),
                nullable(d["total_pos_feedback_count"]),
                nullable(d["skin_tone"]), nullable(d["eye_color"]),
                nullable(d["skin_type"]), nullable(d["hair_color"]),
                nullable(d["product_name"]), nullable(d["brand_name"]),
                nullable(d["price_usd"]), to_bool(d["has_review_text"]),
                to_bool(d["has_review_title"]), nullable(d["source_file"]),
            ))
        with conn.cursor() as cur:
            cur.executemany("""
                INSERT INTO reviews (
                    review_id, product_id, rating, review_title, review_text,
                    is_recommended, helpfulness, submission_time, author_id,
                    total_feedback_count, total_neg_feedback_count,
                    total_pos_feedback_count, skin_tone, eye_color, skin_type,
                    hair_color, product_name_snapshot, brand_name_snapshot,
                    price_usd, has_review_text, has_review_title, source_file
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, rows)
        conn.commit()
        total += len(rows)
        print(f"reviews: {total:,}", flush=True)
    print(f"reviews total: {total:,}")


def load_review_summary(conn):
    df = pd.read_csv(REVIEW_SUMMARY, low_memory=False)
    rows = []
    for r in df.itertuples(index=False):
        d = r._asdict()
        rows.append((
            str(d["product_id"]), nullable(d["review_count"]),
            nullable(d["avg_review_rating"]), nullable(d["recommendation_count"]),
            nullable(d["recommendation_rate"]), nullable(d["avg_helpfulness"]),
            nullable(d["review_text_count"]), nullable(d["review_title_count"]),
            nullable(d["earliest_review"]), nullable(d["latest_review"]),
        ))
    with conn.cursor() as cur:
        cur.executemany("""
            INSERT INTO product_review_summary (
                product_id, review_count, average_review_rating,
                recommendation_count, recommendation_rate,
                average_helpfulness, review_text_count, review_title_count,
                earliest_review_date, latest_review_date
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, rows)
    conn.commit()
    print(f"product_review_summary: {len(rows):,}")


def validate(conn):
    queries = {
        "products": "SELECT COUNT(*) FROM products",
        "ingredients": "SELECT COUNT(*) FROM ingredients",
        "product_ingredients": "SELECT COUNT(*) FROM product_ingredients",
        "ingredient_knowledge": "SELECT COUNT(*) FROM ingredient_knowledge",
        "product_profiles": "SELECT COUNT(*) FROM product_functional_profiles",
        "reviews": "SELECT COUNT(*) FROM reviews",
        "review_summary": "SELECT COUNT(*) FROM product_review_summary",
        "orphan_product_ingredients": """
            SELECT COUNT(*) FROM product_ingredients pi
            LEFT JOIN products p ON p.product_id = pi.product_id
            WHERE p.product_id IS NULL
        """,
        "orphan_ingredients": """
            SELECT COUNT(*) FROM product_ingredients pi
            LEFT JOIN ingredients i ON i.ingredient_id = pi.ingredient_id
            WHERE i.ingredient_id IS NULL
        """,
        "orphan_reviews": """
            SELECT COUNT(*) FROM reviews r
            LEFT JOIN products p ON p.product_id = r.product_id
            WHERE p.product_id IS NULL
        """,
    }
    with conn.cursor() as cur:
        for name, sql in queries.items():
            cur.execute(sql)
            print(f"{name}: {cur.fetchone()[0]:,}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    print("IngredientIQ database loader")
    print(f"Database: {os.getenv('PGDATABASE', 'ingredientiq')}")
    print(f"Products: {PRODUCTS}")
    print(f"Reviews: {REVIEWS}")
    print()

    if not os.getenv("PGPASSWORD"):
        print(
            "ERROR: set PGPASSWORD first.\n"
            "CMD: set PGPASSWORD=your_password\n"
            "PowerShell: $env:PGPASSWORD='your_password'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    with connect() as conn:
        if args.reset:
            clear_database(conn)

        load_products(conn)
        load_ingredients(conn)
        load_product_ingredients(conn)
        load_knowledge(conn)
        load_profiles(conn)
        load_reviews(conn)
        load_review_summary(conn)

        print("\nValidation:")
        validate(conn)

    print("\nDatabase load complete.")


if __name__ == "__main__":
    main()
