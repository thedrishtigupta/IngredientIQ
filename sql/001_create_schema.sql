-- ============================================================
-- IngredientIQ
-- Database Schema v1
-- ============================================================

-- ------------------------------------------------------------
-- 1. PRODUCTS
-- ------------------------------------------------------------

CREATE TABLE products (
    product_id          BIGINT PRIMARY KEY,
    product_name        TEXT NOT NULL,
    brand               TEXT,
    category            TEXT,
    subcategory         TEXT,

    price               NUMERIC(10, 2),
    rating              NUMERIC(3, 2),
    review_count        INTEGER,
    loves_count         INTEGER,

    raw_ingredients     TEXT,

    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);


-- ------------------------------------------------------------
-- 2. INGREDIENTS
-- Canonical ingredient vocabulary
-- ------------------------------------------------------------

CREATE TABLE ingredients (
    ingredient_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    canonical_name      TEXT NOT NULL UNIQUE
);


-- ------------------------------------------------------------
-- 3. PRODUCT <-> INGREDIENT RELATIONSHIP
-- ------------------------------------------------------------

CREATE TABLE product_ingredients (
    product_id              BIGINT NOT NULL,
    ingredient_id           BIGINT NOT NULL,

    position                INTEGER NOT NULL,

    presence_type           TEXT NOT NULL
                            CHECK (
                                presence_type IN (
                                    'PRIMARY',
                                    'MAY_CONTAIN'
                                )
                            ),

    section                 TEXT NOT NULL DEFAULT 'main',

    concentration           NUMERIC(10, 4),
    concentration_unit      TEXT,

    ci_codes                JSONB NOT NULL DEFAULT '[]'::JSONB,
    markers                 JSONB NOT NULL DEFAULT '[]'::JSONB,

    ingredient_raw          TEXT NOT NULL,

    PRIMARY KEY (
        product_id,
        ingredient_id,
        position,
        section
    ),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE,

    FOREIGN KEY (ingredient_id)
        REFERENCES ingredients(ingredient_id)
        ON DELETE RESTRICT
);


-- ------------------------------------------------------------
-- 4. INGREDIENT KNOWLEDGE
-- ------------------------------------------------------------

CREATE TABLE ingredient_knowledge (
    ingredient_id           BIGINT PRIMARY KEY,

    functional_groups       JSONB NOT NULL DEFAULT '[]'::JSONB,
    user_goals              JSONB NOT NULL DEFAULT '[]'::JSONB,
    roles                   JSONB NOT NULL DEFAULT '[]'::JSONB,

    fragrance_related       BOOLEAN NOT NULL DEFAULT FALSE,
    colorant_related        BOOLEAN NOT NULL DEFAULT FALSE,

    notes                   TEXT,
    confidence              NUMERIC(4, 3),

    source                  TEXT,
    knowledge_status        TEXT NOT NULL DEFAULT 'CURATED',

    FOREIGN KEY (ingredient_id)
        REFERENCES ingredients(ingredient_id)
        ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- 5. PRODUCT FUNCTIONAL PROFILES
-- Derived product-level ingredient features
-- ------------------------------------------------------------

CREATE TABLE product_functional_profiles (
    product_id              BIGINT PRIMARY KEY,

    features                JSONB NOT NULL DEFAULT '{}'::JSONB,

    knowledge_version       TEXT,

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- 6. REVIEWS
-- ------------------------------------------------------------

CREATE TABLE reviews (
    review_id               TEXT PRIMARY KEY,

    product_id              BIGINT NOT NULL,

    rating                  SMALLINT
                            CHECK (
                                rating BETWEEN 1 AND 5
                            ),

    review_title            TEXT,
    review_text             TEXT,

    is_recommended          BOOLEAN,

    helpfulness             INTEGER,

    submission_time         DATE,

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE
);


-- ------------------------------------------------------------
-- 7. PRODUCT REVIEW SUMMARY
-- Derived product-level review signals
-- ------------------------------------------------------------

CREATE TABLE product_review_summary (
    product_id                      BIGINT PRIMARY KEY,

    review_count                    INTEGER NOT NULL DEFAULT 0,

    average_review_rating           NUMERIC(4, 3),

    recommendation_count            INTEGER,
    recommendation_rate             NUMERIC(6, 5),

    average_helpfulness             NUMERIC(10, 4),

    review_text_count               INTEGER NOT NULL DEFAULT 0,
    review_title_count              INTEGER NOT NULL DEFAULT 0,

    earliest_review_date            DATE,
    latest_review_date              DATE,

    FOREIGN KEY (product_id)
        REFERENCES products(product_id)
        ON DELETE CASCADE
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_products_category
    ON products(category);

CREATE INDEX idx_products_brand
    ON products(brand);

CREATE INDEX idx_products_price
    ON products(price);

CREATE INDEX idx_products_rating
    ON products(rating);


CREATE INDEX idx_product_ingredients_product
    ON product_ingredients(product_id);

CREATE INDEX idx_product_ingredients_ingredient
    ON product_ingredients(ingredient_id);

CREATE INDEX idx_product_ingredients_presence
    ON product_ingredients(presence_type);


CREATE INDEX idx_ingredient_knowledge_functional_groups
    ON ingredient_knowledge
    USING GIN(functional_groups);

CREATE INDEX idx_ingredient_knowledge_user_goals
    ON ingredient_knowledge
    USING GIN(user_goals);


CREATE INDEX idx_product_profiles_features
    ON product_functional_profiles
    USING GIN(features);


CREATE INDEX idx_reviews_product
    ON reviews(product_id);

CREATE INDEX idx_reviews_rating
    ON reviews(rating);

CREATE INDEX idx_reviews_recommended
    ON reviews(is_recommended);

CREATE INDEX idx_reviews_submission_time
    ON reviews(submission_time);


CREATE INDEX idx_review_summary_rating
    ON product_review_summary(average_review_rating);

CREATE INDEX idx_review_summary_recommendation
    ON product_review_summary(recommendation_rate);