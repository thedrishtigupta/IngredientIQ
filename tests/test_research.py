import numpy as np
import pandas as pd
import pytest

from research.combos import PRESPECIFIED, add_combo_features, mine_combinations
from research.dataset import (MIN_REVIEWS_FOR_RATING, build_study_data, canonical_ingredient,
                              family_key, pretty_feature)
from research.explain import feature_group
from research.models import corrected_ttest
from research.stats import adjusted_effects, bh, cliffs_delta_from_u


# ---------------------------------------------------------------- dataset

@pytest.mark.parametrize("raw, expected", [
    ("Aqua/Water/Eau", "water"),
    ("water", "water"),
    ("Parfum (Fragrance)", "fragrance"),
    ("Caprylic/Capric Triglyceride", "caprylic/capric triglyceride"),
    ("1", None),
    ("*", None),
    (None, None),
])
def test_canonical_ingredient(raw, expected):
    assert canonical_ingredient(raw) == expected


def test_family_key_ignores_size_words():
    assert family_key("Glow", "Mini Dew Drops 1 oz") == family_key("Glow", "Dew Drops")
    assert family_key("Glow", "Dew Drops") != family_key("Other", "Dew Drops")


def test_pretty_feature():
    assert pretty_feature("ing__glycerin") == "glycerin"
    assert pretty_feature("fg__fragrance_component") == "share of fragrance component"
    assert pretty_feature("cat__brand_name_Tatcha") == "brand: Tatcha"
    assert pretty_feature("num__fg__uv_filter") == "share of uv filter"
    assert pretty_feature("num__pos__linalool") == "position: linalool"
    assert pretty_feature("num__log_price") == "log price"
    assert feature_group("num__pos__glycerin") == "ingredient"
    assert feature_group("cat__brand_name_Tatcha") == "baseline"


def _sources():
    """Five products: two share a formula (full size + mini), one is a gift set."""
    products = pd.DataFrame({
        "product_id": ["P1", "P2", "P3", "P4", "P5"],
        "product_name": ["Dew Cream", "Mini Dew Cream", "Glow Serum", "Holiday Set", "Clay Mask"],
        "brand_name": ["A", "A", "B", "B", "C"],
        "loves_count": [1000, 50, 300, 10, 20],
        "rating": [4.5, 4.4, 4.0, 3.0, 3.9],
        "reviews": [400, 5, 100, 3, 10],
        "price_usd": [40, 15, 30, 60, 25],
        "value_price_usd": [40, 15, 30, 80, 25],
        "sale_price_usd": [np.nan] * 5,
        "variation_type": [np.nan] * 5,
        "limited_edition": 0, "new": 0, "online_only": 0, "out_of_stock": 0,
        "sephora_exclusive": 0, "child_count": 0,
        "primary_category": "Skincare",
        "secondary_category": ["Moisturizers", "Moisturizers", "Treatments", "Value & Gift Sets", "Masks"],
        "tertiary_category": np.nan,
    })
    rows = []
    for pid, names in {"P1": ["Water", "Glycerin"], "P2": ["Aqua", "Glycerin"],
                       "P3": ["Water", "Niacinamide"], "P4": ["Water"], "P5": ["Kaolin", "Water"]}.items():
        rows += [{"product_id": pid, "normalized_name": n, "position": i + 1,
                  "presence_type": "PRIMARY", "section": "main"} for i, n in enumerate(names)]
    functional = pd.DataFrame({"product_id": ["P1", "P2", "P3", "P4", "P5"],
                               "total_ingredient_occurrences": [2, 2, 2, 1, 2],
                               "fg_humectant": [1, 1, 0, 0, 0]})
    reviews = pd.DataFrame({"product_id": ["P1"], "recommendation_rate": [0.9],
                            "recommendation_denominator": [300]})
    return {"products": products, "ingredients": pd.DataFrame(rows),
            "functional": functional, "reviews": reviews}


def test_build_study_data_scope_dedup_and_targets():
    study = build_study_data(_sources())
    f = study.frame.set_index("product_id")
    # gift set excluded; mini merged into its full size (same brand + formula), most reviews kept
    assert set(f.index) == {"P1", "P3", "P5"}
    # ratings from fewer than MIN_REVIEWS_FOR_RATING reviews are not used as a target
    assert MIN_REVIEWS_FOR_RATING > 10
    assert np.isnan(f.loc["P5", "rating"])
    assert f.loc["P1", "rating"] == 4.5
    assert f.loc["P1", "rec_rate"] == 0.9 and np.isnan(f.loc["P3", "rec_rate"])
    # "Water" and "Aqua" are one ingredient; prominence 1 for the first ingredient
    assert f.loc["P1", "ing__water"] == 1 and f.loc["P1", "pos__water"] == 1.0
    assert f.loc["P5", "pos__water"] == pytest.approx(0.5)
    assert f["fg__humectant"].loc["P1"] == pytest.approx(0.5)


# ---------------------------------------------------------------- combinations

def test_mining_finds_pairs_that_always_occur_together():
    rng = np.random.default_rng(0)
    n = 400
    a = rng.random(n) < 0.3
    frame = pd.DataFrame({
        "primary_category": "Skincare",
        "ing__a": a, "ing__b": a,                      # always together
        "ing__c": rng.random(n) < 0.3,                 # independent
        "ing__glycerin": rng.random(n) < 0.5,
        "ing__sodium hyaluronate": rng.random(n) < 0.5,
    }).astype({c: int for c in ["ing__a", "ing__b", "ing__c", "ing__glycerin", "ing__sodium hyaluronate"]})
    combos = mine_combinations(frame, ["ing__a", "ing__b", "ing__c", "ing__glycerin", "ing__sodium hyaluronate"])
    found = set(combos["items"])
    assert ("a", "b") in found
    assert ("a", "c") not in found                     # lift ~1: chance co-occurrence
    assert combos.loc[combos.prespecified, "items"].tolist() == [("glycerin", "sodium hyaluronate")]
    out, cols = add_combo_features(frame, combos)
    assert (out["combo__a + b"] == frame.ing__a).all()
    assert any(p == ("glycerin", "sodium hyaluronate") for p in PRESPECIFIED)


# ---------------------------------------------------------------- statistics

def test_cliffs_delta_bounds():
    assert cliffs_delta_from_u(100, 10, 10) == 1
    assert cliffs_delta_from_u(0, 10, 10) == -1
    assert cliffs_delta_from_u(50, 10, 10) == 0


def test_bh_keeps_nan_and_is_monotone():
    p = np.array([0.01, np.nan, 0.04, 0.03])
    q = bh(p)
    assert np.isnan(q[1])
    assert q[0] <= q[3] <= q[2]
    assert (q[[0, 2, 3]] >= p[[0, 2, 3]]).all()          # correcting never lowers a p-value


def test_adjustment_removes_a_pure_brand_effect():
    """Ingredient X is used only by the popular brand; within a brand it changes nothing."""
    rng = np.random.default_rng(1)
    n = 600
    brand = np.where(rng.random(n) < 0.5, "Popular", "Niche")
    popular = brand == "Popular"
    x = np.where(popular, rng.random(n) < 0.8, rng.random(n) < 0.1).astype(int)
    real = rng.integers(0, 2, n)                        # an ingredient with a true effect
    y = 2.0 * popular + 0.5 * real + rng.normal(0, 1, n)
    sub = pd.DataFrame({"brand_name": brand, "secondary_category": "Moisturizers",
                        "log_price": rng.normal(3, 0.3, n), "ing__x": x, "ing__real": real})

    raw_gap = y[x == 1].mean() - y[x == 0].mean()
    beta, se, p, lo, hi = adjusted_effects(sub, pd.Series(y), ["ing__x", "ing__real"])
    assert raw_gap > 1                                   # looks hugely "successful" raw
    assert abs(beta[0]) < 0.15 and p[0] > 0.01           # ... but not once brand is fixed
    assert lo[0] < 0 < hi[0]                             # and its 95% CI covers zero
    assert beta[1] > 0.2 and p[1] < 1e-6                 # the real effect survives
    assert lo[1] > 0 and (se > 0).all()


# ---------------------------------------------------------------- model comparison

def test_corrected_ttest_is_more_conservative_than_paired():
    from scipy import stats
    diffs = np.array([0.02, 0.03, 0.01, 0.025, 0.015, 0.02, 0.03, 0.01, 0.02, 0.025])
    naive = stats.ttest_1samp(diffs, 0).pvalue
    corrected = corrected_ttest(diffs, n_train=4000, n_test=1000)
    assert corrected > naive
    assert np.isnan(corrected_ttest(np.zeros(5), 100, 25))
