"""Steps 1-2: build the analysis table, one row per product.

What happens, in order:
1. Load the catalogue, the parsed ingredient rows, the functional profiles and
   the review summary.
2. Keep only products the study can say something about: they have an
   ingredient list, are a single formula (not a kit / gift set / tool), and are
   not a mini or duplicate of a product we already have.
3. Add the success targets (rating, loves, reviews, recommendation rate and a
   composite "high performer" label).
4. Add the baseline (non-ingredient) features and the ingredient features.

Duplicates matter: a mini and its full size share one formula. If both stayed,
the same formula would sit in the training and the test fold and make the
ingredient model look better than it is. So products are grouped into
families and one product per family is kept.
"""

from dataclasses import dataclass, field
import re

import numpy as np
import pandas as pd

MIN_REVIEWS_FOR_RATING = 25       # ratings from fewer reviews are mostly noise
MIN_RECOMMENDATION_VOTES = 25     # same rule for the recommendation rate
TOP_INGREDIENTS = 300             # ingredient presence features
TOP_PROMINENCE = 100              # of those, also a "how high in the list" feature
HIGH_PERFORMER_QUANTILE = 0.75    # top quarter within its category = 1

EXCLUDED_PRIMARY = {"Mini Size", "Tools & Brushes", "Gifts"}
EXCLUDED_SECONDARY = {"Value & Gift Sets", "Mini Size"}

BASE_CATEGORICAL = ["brand_name", "primary_category", "secondary_category", "tertiary_category"]
BASE_NUMERIC = [
    "log_price", "has_value_price", "on_sale", "limited_edition", "new", "online_only",
    "out_of_stock", "sephora_exclusive", "child_count", "has_variations",
]

# Existing popularity is part of Model A only where it is not the target itself
# (or a near copy of it). Loves and review count move together, so neither may
# predict the other; the composite label is built from all three.
POPULARITY_CONTROLS = {
    "rating": ["log_loves", "log_reviews"],
    "rec_rate": ["log_loves", "log_reviews"],
    "log_loves": [],
    "log_reviews": [],
    "high_performer": [],
}
TARGETS = {
    # name: (task, label for reports)
    "rating": ("regression", "Average rating"),
    "log_loves": ("regression", "Popularity (log loves)"),
    "log_reviews": ("regression", "Review count (log)"),
    "rec_rate": ("regression", "Recommendation rate"),
    "high_performer": ("classification", "High performer (top 25% composite)"),
}

_WATER = {"water", "aqua", "eau"}
_FRAGRANCE = {"fragrance", "parfum", "perfume", "aroma"}
_SIZE_WORDS = re.compile(
    r"\b(mini|travel[- ]size|travel|jumbo|value[- ]size|refill|deluxe|full[- ]size|"
    r"\d+(\.\d+)?\s?(ml|oz|g|fl))\b"
)


def canonical_ingredient(name):
    """Merge spellings that are the same ingredient; drop parser junk ("1", "*").

    >>> canonical_ingredient("Aqua/Water/Eau"), canonical_ingredient("Parfum (Fragrance)")
    ('water', 'fragrance')
    """
    if not isinstance(name, str):
        return None
    n = re.sub(r"\s+", " ", name.lower()).strip(" .*-•")
    if len(n) < 3 or re.fullmatch(r"[\d\W_]+", n):
        return None
    parts = {p.strip() for p in re.split(r"[/()]", n) if p.strip()}
    if parts and parts <= _WATER:
        return "water"
    if parts and parts <= _FRAGRANCE:
        return "fragrance"
    return n


def family_key(brand, name):
    """Brand + product name without size words: 'Mini Lip Oil' -> 'brand|lip oil'."""
    n = _SIZE_WORDS.sub(" ", str(name).lower())
    n = re.sub(r"\([^)]*\)", " ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return f"{str(brand).lower()}|{' '.join(n.split())}"


def _families(df):
    """Union products sharing a name family OR an identical ingredient list in one brand."""
    parent = list(range(len(df)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for key in ["name_family", "formula_key"]:
        for idx in df.groupby(key, sort=False).indices.values():
            for j in idx[1:]:
                parent[find(j)] = find(idx[0])
    return np.array([find(i) for i in range(len(df))])


@dataclass
class StudyData:
    """The analysis table plus the names of each feature group."""

    frame: pd.DataFrame
    ingredient_cols: list[str]
    prominence_cols: list[str]
    functional_cols: list[str]
    combo_cols: list[str] = field(default_factory=list)
    notes: dict = field(default_factory=dict)

    @property
    def ingredient_feature_cols(self):
        """Everything Model B adds on top of Model A."""
        return (["n_ingredients"] + self.ingredient_cols + self.prominence_cols
                + self.functional_cols + self.combo_cols)


def load_sources(data_dir):
    raw = data_dir / "raw"
    processed = data_dir / "processed"
    return {
        "products": pd.read_csv(raw / "product_info.csv"),
        "ingredients": pd.read_csv(processed / "product_ingredients.csv", low_memory=False,
                                   usecols=["product_id", "normalized_name", "position",
                                            "presence_type", "section"]),
        "functional": pd.read_csv(processed / "product_functional_profile_v2.csv"),
        "reviews": pd.read_csv(processed / "product_review_summary.csv"),
    }


def build_study_data(sources, min_reviews=MIN_REVIEWS_FOR_RATING, dedup=True):
    """The analysis table. The two options exist for the sensitivity analysis:
    min_reviews replaces both reliability thresholds (rating and recommendation
    votes); dedup=False keeps every family member (minis, re-listings)."""
    products = sources["products"].copy()
    notes = {"catalogue_products": len(products)}

    # --- ingredient rows: primary ingredients of single-formula products only
    ing = sources["ingredients"]
    ing = ing[ing.presence_type == "PRIMARY"].copy()
    sections = ing.groupby("product_id").section.nunique()
    multi = set(sections[sections > 1].index)
    ing = ing[~ing.product_id.isin(multi)]
    ing["ingredient"] = ing.normalized_name.map(canonical_ingredient)
    ing = ing.dropna(subset=["ingredient"]).sort_values(["product_id", "position"])
    ing = ing.drop_duplicates(["product_id", "ingredient"])  # keep first (highest) position
    ing["rank"] = ing.groupby("product_id").cumcount()
    ing["n"] = ing.groupby("product_id").ingredient.transform("size")
    ing["prominence"] = 1 - ing["rank"] / ing["n"]  # first ingredient = 1, last ~ 0

    # --- scope filter
    keep = (
        products.product_id.isin(ing.product_id)
        & ~products.primary_category.isin(EXCLUDED_PRIMARY)
        & ~products.secondary_category.isin(EXCLUDED_SECONDARY)
    )
    notes["no_ingredients"] = int((~products.product_id.isin(sources["ingredients"].product_id)).sum())
    notes["multi_component_kits"] = int(products.product_id.isin(multi).sum())
    products = products[keep].reset_index(drop=True)
    notes["in_scope_before_dedup"] = len(products)

    # --- one product per family (most reviews wins)
    formula = ing.groupby("product_id").ingredient.apply(lambda s: "|".join(sorted(s)))
    products["name_family"] = [family_key(b, n) for b, n in zip(products.brand_name, products.product_name)]
    products["formula_key"] = products.brand_name.str.lower() + "#" + products.product_id.map(formula)
    products["family"] = _families(products)
    products["reviews"] = products.reviews.fillna(0)
    if dedup:
        products = (products.sort_values(["family", "reviews", "loves_count"], ascending=False)
                    .drop_duplicates("family").sort_values("product_id").reset_index(drop=True))
    notes["analysis_products"] = len(products)
    ing = ing[ing.product_id.isin(products.product_id)]

    frame = _add_targets(products, sources["reviews"], min_reviews)
    frame = _add_baseline_features(frame)
    frame, ingredient_cols, prominence_cols = _add_ingredient_features(frame, ing)
    frame, functional_cols = _add_functional_features(frame, sources["functional"])
    notes["targets_available"] = {t: int(frame[t].notna().sum()) for t in TARGETS}
    return StudyData(frame, ingredient_cols, prominence_cols, functional_cols, notes=notes)


def _add_targets(df, review_summary, min_reviews=MIN_REVIEWS_FOR_RATING):
    df = df.copy()
    df["log_loves"] = np.log1p(df.loves_count)
    df["log_reviews"] = np.log1p(df.reviews)
    catalog_rating = df.rating
    df["rating"] = df.rating.where(df.reviews >= min_reviews)

    rs = review_summary.set_index("product_id")
    min_votes = MIN_RECOMMENDATION_VOTES if min_reviews == MIN_REVIEWS_FOR_RATING else min_reviews
    rate = rs.recommendation_rate.where(rs.recommendation_denominator >= min_votes)
    df["rec_rate"] = df.product_id.map(rate)

    # Composite: within its own category, how does a product rank on (shrunk)
    # rating, loves and reviews? Average of the three percentiles, top quarter = 1.
    # Shrinking pulls a rating from few reviews toward the category average.
    category_mean = catalog_rating.groupby(df.primary_category).transform("mean")
    w = df.reviews / (df.reviews + MIN_REVIEWS_FOR_RATING)
    df["_shrunk_rating"] = (w * catalog_rating.fillna(category_mean) + (1 - w) * category_mean)
    parts = [df.groupby("primary_category")[c].rank(pct=True)
             for c in ["_shrunk_rating", "log_loves", "log_reviews"]]
    df["success_score"] = sum(parts) / 3
    cut = df.groupby("primary_category").success_score.transform(
        lambda s: s.quantile(HIGH_PERFORMER_QUANTILE))
    df["high_performer"] = (df.success_score >= cut).astype(int)
    return df.drop(columns="_shrunk_rating")


def _add_baseline_features(df):
    df = df.copy()
    df["log_price"] = np.log1p(df.price_usd)
    df["has_value_price"] = (df.value_price_usd.notna() & (df.value_price_usd != df.price_usd)).astype(int)
    df["on_sale"] = df.sale_price_usd.notna().astype(int)
    df["has_variations"] = df.variation_type.notna().astype(int)
    for c in ["limited_edition", "new", "online_only", "out_of_stock", "sephora_exclusive", "child_count"]:
        df[c] = df[c].fillna(0).astype(int)
    for c in BASE_CATEGORICAL:
        df[c] = df[c].fillna("Unknown").astype(str)
    return df


def _add_ingredient_features(df, ing):
    counts = ing.ingredient.value_counts()
    top = list(counts.index[:TOP_INGREDIENTS])
    sub = ing[ing.ingredient.isin(top)]
    prom = sub.pivot_table(index="product_id", columns="ingredient", values="prominence", aggfunc="max")
    prom = prom.reindex(index=df.product_id, columns=top).fillna(0.0)

    presence = (prom > 0).astype(np.int8)
    presence.columns = [f"ing__{c}" for c in top]
    prominence = prom[top[:TOP_PROMINENCE]]
    prominence.columns = [f"pos__{c}" for c in top[:TOP_PROMINENCE]]

    n_ing = ing.groupby("product_id").size().reindex(df.product_id).fillna(0).values
    out = pd.concat([df.reset_index(drop=True), presence.reset_index(drop=True),
                     prominence.reset_index(drop=True)], axis=1)
    out["n_ingredients"] = n_ing
    return out, list(presence.columns), list(prominence.columns)


def _add_functional_features(df, functional):
    """Share of each product's ingredients in each functional group (e.g. humectants)."""
    fg = [c for c in functional.columns if c.startswith("fg_") and not c.startswith("fg_primary_")]
    f = functional.set_index("product_id")
    total = f.total_ingredient_occurrences.replace(0, np.nan)
    shares = f[fg].div(total, axis=0).fillna(0)
    shares.columns = [f"fg__{c[3:]}" for c in fg]
    shares = shares.reindex(df.product_id).fillna(0).reset_index(drop=True)
    # drop groups (almost) nobody has: they cannot be tested or learned
    shares = shares.loc[:, (shares > 0).mean() >= 0.01]
    return pd.concat([df, shares], axis=1), list(shares.columns)


def pretty_feature(col):
    """Column name -> label a reader understands."""
    if col.startswith(("num__", "cat__")):  # prefix added by the model pipeline
        col = col[5:]
    if col.startswith(("ing__", "combo__")):
        return col.split("__", 1)[1]
    if col.startswith("pos__"):
        return "position: " + col[5:]
    if col.startswith("fg__"):
        return "share of " + col[4:].replace("_", " ")
    for c in BASE_CATEGORICAL:
        if col.startswith(c + "_"):
            return f"{c.replace('_name', '').replace('_', ' ')}: {col[len(c) + 1:]}"
    return col.replace("_", " ")
