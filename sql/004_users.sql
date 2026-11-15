-- IngredientIQ Migration 004: user accounts, profiles, search history, saved products.
-- Safe to re-run (IF NOT EXISTS everywhere). The API also applies it at startup.

CREATE TABLE IF NOT EXISTS users (
    user_id         BIGSERIAL PRIMARY KEY,
    email           TEXT NOT NULL,                  -- stored lower-cased
    display_name    TEXT NOT NULL,
    password_hash   TEXT NOT NULL,                  -- "scrypt$n$r$p$salt$hash" (see src/api/auth.py)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (lower(email));

-- One row per signed-in browser. Only a SHA-256 of the token is stored, never the token itself.
CREATE TABLE IF NOT EXISTS user_sessions (
    token_hash      TEXT PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions (user_id);

-- Preferences used to personalise searches. Every field is optional.
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id             BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    skin_type           TEXT,                       -- dry, oily, combination, normal, sensitive
    goals               TEXT[] NOT NULL DEFAULT '{}',   -- ids from GOAL_LABELS
    avoided_ingredients TEXT[] NOT NULL DEFAULT '{}',
    fragrance_free      BOOLEAN NOT NULL DEFAULT FALSE,
    max_price           NUMERIC(8, 2),
    preferred_category  TEXT,
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- What the user searched for. kind = 'text' (name/brand search) or 'recommend' (goals + filters).
CREATE TABLE IF NOT EXISTS search_history (
    search_id       BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    kind            TEXT NOT NULL CHECK (kind IN ('text', 'recommend')),
    query           TEXT NOT NULL,                  -- the typed text, or a readable summary of the filters
    params          JSONB NOT NULL DEFAULT '{}'::JSONB,  -- the full request, so it can be run again
    result_count    INTEGER NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history (user_id, created_at DESC);

CREATE TABLE IF NOT EXISTS saved_products (
    user_id         BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id      TEXT NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, product_id)
);
