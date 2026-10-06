"""Score every review with VADER and write one row per product to product_review_signals.

Reviews are streamed from Postgres in batches (never all 1M texts in memory),
added to per-product totals, then written with an upsert.

Run:  python scripts/run_review_nlp.py            (full run)
      python scripts/run_review_nlp.py --limit 20000   (quick test, writes nothing)
"""

import argparse
import os
from pathlib import Path
import sys
import time

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews.sentiment import METHOD, add_review, build_signal, new_totals

load_dotenv()

BATCH_SIZE = 5000

UPSERT = """
    INSERT INTO product_review_signals
        (product_id, review_count, analyzed_count, avg_sentiment, positive_share,
         negative_share, review_score, aspects, method)
    VALUES
        (%(product_id)s, %(review_count)s, %(analyzed_count)s, %(avg_sentiment)s,
         %(positive_share)s, %(negative_share)s, %(review_score)s, %(aspects)s, %(method)s)
    ON CONFLICT (product_id) DO UPDATE SET
        review_count = EXCLUDED.review_count,
        analyzed_count = EXCLUDED.analyzed_count,
        avg_sentiment = EXCLUDED.avg_sentiment,
        positive_share = EXCLUDED.positive_share,
        negative_share = EXCLUDED.negative_share,
        review_score = EXCLUDED.review_score,
        aspects = EXCLUDED.aspects,
        method = EXCLUDED.method,
        computed_at = CURRENT_TIMESTAMP
"""


def connect():
    return psycopg.connect(
        host=os.getenv("PGHOST", "localhost"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE", "ingredientiq"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD"),
    )


def score_reviews(conn, limit=None):
    """Stream reviews through a server-side cursor; return totals per product."""
    query = "SELECT product_id, review_title, review_text FROM reviews"
    if limit:
        query += f" LIMIT {int(limit)}"

    totals = {}
    done = 0
    start = time.time()
    with conn.cursor(name="review_stream") as cur:  # named = server-side cursor
        cur.execute(query)
        while True:
            rows = cur.fetchmany(BATCH_SIZE)
            if not rows:
                break
            for product_id, title, text in rows:
                add_review(totals.setdefault(product_id, new_totals()), title, text)
            done += len(rows)
            print(f"  {done:,} reviews scored ({time.time() - start:.0f}s)")
    return totals


def write_signals(conn, totals):
    """Upsert one row per product. The caller commits."""
    # Global average of the 0..1 score over all scored reviews: smoothing pulls toward it.
    scored = sum(t["analyzed_count"] for t in totals.values())
    total_sentiment = sum(t["sentiment_sum"] for t in totals.values())
    global_score = (total_sentiment / scored + 1) / 2
    print(f"Global average review score: {global_score:.4f}")

    with conn.cursor() as cur:
        for product_id, product_totals in totals.items():
            signal = build_signal(product_totals, global_score)
            signal["product_id"] = product_id
            signal["aspects"] = Jsonb(signal["aspects"])
            signal["method"] = METHOD
            cur.execute(UPSERT, signal)
    return len(totals)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="only score the first N reviews (writes nothing)")
    args = parser.parse_args()

    with connect() as conn:
        totals = score_reviews(conn, args.limit)
        print(f"Products with reviews: {len(totals):,}")
        if args.limit:
            print("--limit given: nothing written to the database.")
            return
        rows = write_signals(conn, totals)
    print(f"Wrote {rows:,} rows to product_review_signals.")


if __name__ == "__main__":
    main()
