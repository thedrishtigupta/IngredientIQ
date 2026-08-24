-- IngredientIQ Database Integration
-- Migration 002: preserve full catalog/review fields and correct product IDs.
--
-- IMPORTANT:
-- The Sephora product IDs are strings such as P473671, NOT numeric IDs.
-- The original v1 schema used BIGINT for product_id; this migration changes
-- every product_id column to TEXT before any data is loaded.

-- Drop foreign keys temporarily so the referenced column types can change.
ALTER TABLE product_ingredients
    DROP CONSTRAINT IF EXISTS product_ingredients_product_id_fkey;

ALTER TABLE product_ingredients
    DROP CONSTRAINT IF EXISTS product_ingredients_ingredient_id_fkey;

ALTER TABLE ingredient_knowledge
    DROP CONSTRAINT IF EXISTS ingredient_knowledge_ingredient_id_fkey;

ALTER TABLE product_functional_profiles
    DROP CONSTRAINT IF EXISTS product_functional_profiles_product_id_fkey;

ALTER TABLE reviews
    DROP CONSTRAINT IF EXISTS reviews_product_id_fkey;

ALTER TABLE product_review_summary
    DROP CONSTRAINT IF EXISTS product_review_summary_product_id_fkey;


-- Correct product_id type.
ALTER TABLE products
    ALTER COLUMN product_id TYPE TEXT
    USING product_id::TEXT;

ALTER TABLE product_ingredients
    ALTER COLUMN product_id TYPE TEXT
    USING product_id::TEXT;

ALTER TABLE product_functional_profiles
    ALTER COLUMN product_id TYPE TEXT
    USING product_id::TEXT;

ALTER TABLE reviews
    ALTER COLUMN product_id TYPE TEXT
    USING product_id::TEXT;

ALTER TABLE product_review_summary
    ALTER COLUMN product_id TYPE TEXT
    USING product_id::TEXT;


-- Restore foreign keys.
ALTER TABLE product_ingredients
    ADD CONSTRAINT product_ingredients_product_id_fkey
    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE;

ALTER TABLE product_ingredients
    ADD CONSTRAINT product_ingredients_ingredient_id_fkey
    FOREIGN KEY (ingredient_id)
    REFERENCES ingredients(ingredient_id)
    ON DELETE RESTRICT;

ALTER TABLE ingredient_knowledge
    ADD CONSTRAINT ingredient_knowledge_ingredient_id_fkey
    FOREIGN KEY (ingredient_id)
    REFERENCES ingredients(ingredient_id)
    ON DELETE CASCADE;

ALTER TABLE product_functional_profiles
    ADD CONSTRAINT product_functional_profiles_product_id_fkey
    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE;

ALTER TABLE reviews
    ADD CONSTRAINT reviews_product_id_fkey
    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE;

ALTER TABLE product_review_summary
    ADD CONSTRAINT product_review_summary_product_id_fkey
    FOREIGN KEY (product_id)
    REFERENCES products(product_id)
    ON DELETE CASCADE;


-- Preserve the full catalog metadata from product_info.csv.
ALTER TABLE products
    ADD COLUMN IF NOT EXISTS brand_id BIGINT,
    ADD COLUMN IF NOT EXISTS variation_type TEXT,
    ADD COLUMN IF NOT EXISTS variation_value TEXT,
    ADD COLUMN IF NOT EXISTS variation_desc TEXT,
    ADD COLUMN IF NOT EXISTS value_price_usd NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS sale_price_usd NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS limited_edition BOOLEAN,
    ADD COLUMN IF NOT EXISTS is_new BOOLEAN,
    ADD COLUMN IF NOT EXISTS online_only BOOLEAN,
    ADD COLUMN IF NOT EXISTS out_of_stock BOOLEAN,
    ADD COLUMN IF NOT EXISTS sephora_exclusive BOOLEAN,
    ADD COLUMN IF NOT EXISTS highlights JSONB,
    ADD COLUMN IF NOT EXISTS tertiary_category TEXT,
    ADD COLUMN IF NOT EXISTS child_count INTEGER,
    ADD COLUMN IF NOT EXISTS child_max_price NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS child_min_price NUMERIC(10,2);


-- Preserve the cleaned review fields.
ALTER TABLE reviews
    ADD COLUMN IF NOT EXISTS author_id TEXT,
    ADD COLUMN IF NOT EXISTS total_feedback_count INTEGER,
    ADD COLUMN IF NOT EXISTS total_neg_feedback_count INTEGER,
    ADD COLUMN IF NOT EXISTS total_pos_feedback_count INTEGER,
    ADD COLUMN IF NOT EXISTS skin_tone TEXT,
    ADD COLUMN IF NOT EXISTS eye_color TEXT,
    ADD COLUMN IF NOT EXISTS skin_type TEXT,
    ADD COLUMN IF NOT EXISTS hair_color TEXT,
    ADD COLUMN IF NOT EXISTS product_name_snapshot TEXT,
    ADD COLUMN IF NOT EXISTS brand_name_snapshot TEXT,
    ADD COLUMN IF NOT EXISTS price_usd NUMERIC(10,2),
    ADD COLUMN IF NOT EXISTS has_review_text BOOLEAN,
    ADD COLUMN IF NOT EXISTS has_review_title BOOLEAN,
    ADD COLUMN IF NOT EXISTS source_file TEXT;


-- Useful application/query indexes.
CREATE INDEX IF NOT EXISTS idx_products_category
    ON products(category);

CREATE INDEX IF NOT EXISTS idx_products_subcategory
    ON products(subcategory);

CREATE INDEX IF NOT EXISTS idx_products_brand
    ON products(brand);

CREATE INDEX IF NOT EXISTS idx_products_brand_id
    ON products(brand_id);

CREATE INDEX IF NOT EXISTS idx_products_price
    ON products(price);

CREATE INDEX IF NOT EXISTS idx_products_rating
    ON products(rating);

CREATE INDEX IF NOT EXISTS idx_product_ingredients_product
    ON product_ingredients(product_id);

CREATE INDEX IF NOT EXISTS idx_product_ingredients_ingredient
    ON product_ingredients(ingredient_id);

CREATE INDEX IF NOT EXISTS idx_product_ingredients_presence
    ON product_ingredients(presence_type);

CREATE INDEX IF NOT EXISTS idx_ingredient_knowledge_functional_groups
    ON ingredient_knowledge USING GIN(functional_groups);

CREATE INDEX IF NOT EXISTS idx_ingredient_knowledge_user_goals
    ON ingredient_knowledge USING GIN(user_goals);

CREATE INDEX IF NOT EXISTS idx_product_profiles_features
    ON product_functional_profiles USING GIN(features);

CREATE INDEX IF NOT EXISTS idx_reviews_product
    ON reviews(product_id);

CREATE INDEX IF NOT EXISTS idx_reviews_product_date
    ON reviews(product_id, submission_time);

CREATE INDEX IF NOT EXISTS idx_reviews_rating
    ON reviews(rating);

CREATE INDEX IF NOT EXISTS idx_reviews_recommended
    ON reviews(is_recommended);

CREATE INDEX IF NOT EXISTS idx_reviews_submission_time
    ON reviews(submission_time);

CREATE INDEX IF NOT EXISTS idx_review_summary_rating
    ON product_review_summary(average_review_rating);

CREATE INDEX IF NOT EXISTS idx_review_summary_recommendation
    ON product_review_summary(recommendation_rate);
