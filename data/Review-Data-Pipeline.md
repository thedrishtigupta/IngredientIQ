# IngredientIQ — Phase 3: Review Data Pipeline

## Scope

This phase merges and validates the five supplied review CSV files and prepares product-level review signals for later recommendation and review-NLP stages.

## Source files

- `reviews_0-250.csv`
- `reviews_250-500.csv`
- `reviews_500-750.csv`
- `reviews_750-1250.csv`
- `reviews_1250-end.csv`

All five files share the same 19-column schema. `Unnamed: 0` is a source-row index and is not part of the review entity.

## Observed dataset

- Raw review rows: **1,094,411**
- Unique products represented: **2,351**
- Catalog products: **8,494**
- Review products missing from catalog: **0**
- Review text missing: **1,444**
- Review title missing: **310,654**
- Recommendation flag missing: **167,988**
- Ratings: 1–5 only
- Review dates: 2008-08-28 through 2023-03-21

The supplied review data is therefore substantially larger than the ~119k / ~499-product subset described in the current synopsis. The implementation should use the actual supplied files as the data source and preserve this distinction in project documentation.

## Cleaning decisions

1. Merge all five files using the common schema.
2. Remove the source-only `Unnamed: 0` field.
3. Normalize identifiers and metadata by trimming surrounding whitespace.
4. Parse `submission_time` as a date.
5. Coerce numeric fields (`rating`, recommendation flag, helpfulness and feedback counts) to numeric types.
6. Preserve missing review text/title rather than deleting those reviews.
7. Deduplicate using a stable review identity based on author, product, date, review content (or title when text is missing), and rating.
8. Preserve `source_file` for traceability.
9. Generate a stable SHA-256 `review_id`.
10. Produce a product-level summary for later recommendation and NLP stages.

## Product-level review signals

`product_review_summary.csv` contains:

- review count
- average review rating
- recommendation count
- recommendation denominator
- recommendation rate
- average helpfulness
- helpfulness count
- review-text count
- review-title count
- earliest review
- latest review
- catalog review count
- catalog rating
- catalog loves count
- review-count gap vs catalog

## Important interpretation

The review dataset is not a complete copy of the catalog's review history. For the 2,351 represented products, review counts are generally close to the catalog `reviews` field, but not always identical. This should be treated as a dataset-coverage difference, not automatically as an error.

The review-derived recommendation rate is available for the represented products because the review files contain recommendation flags. Products outside this subset should not be assigned fabricated review-derived signals.

## Next review stage

After this data-engineering layer is frozen:

`clean reviews -> review NLP -> aspect/theme extraction -> product-level experience signals`

Only after that should review-derived signals be integrated into the hybrid recommender.
