-- IngredientIQ Migration 003: review NLP output (one row per product).
-- Filled by scripts/run_review_nlp.py. Products without reviews have NO row
-- (we never invent review signals for them).

CREATE TABLE IF NOT EXISTS product_review_signals (
    product_id      TEXT PRIMARY KEY
                    REFERENCES products(product_id) ON DELETE CASCADE,

    review_count    INTEGER NOT NULL,           -- reviews for this product
    analyzed_count  INTEGER NOT NULL,           -- reviews that had text and were scored

    avg_sentiment   NUMERIC(5, 4),              -- mean sentiment, -1 .. 1
    positive_share  NUMERIC(5, 4),              -- share of reviews with sentiment > 0.05
    negative_share  NUMERIC(5, 4),              -- share of reviews with sentiment < -0.05

    review_score    NUMERIC(5, 4),              -- 0 .. 1, smoothed; used by the hybrid recommender

    aspects         JSONB NOT NULL DEFAULT '{}'::JSONB,
    -- {"hydration": {"mentions": 120, "positive_share": 0.91}, "scent": {...}}

    method          TEXT NOT NULL,              -- e.g. 'vader_v1'
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_signals_score
    ON product_review_signals(review_score);
