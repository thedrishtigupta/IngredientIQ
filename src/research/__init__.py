"""Research track: do ingredients predict product success? (synopsis section 2.6).

Kept separate from the recommender on purpose: it reads the processed CSVs,
not the database, and no LLM is involved, so every number can be rebuilt with
`python scripts/run_research.py`.

    dataset.py   step 1-2  one row per product, targets + features
    combos.py    step 4    frequent ingredient combinations (FP-Growth)
    stats.py     step 3    association tests with BH correction + effect sizes
    models.py    step 5    Model A (metadata) vs Model B (+ ingredients)
    explain.py   step 6    SHAP importance, cross-checked against step 3
"""
