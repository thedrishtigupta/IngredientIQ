"""Step 4: ingredient combinations worth testing, found with FP-Growth.

Testing every pair of 300 ingredients would be ~45,000 tests, most of them
for pairs that barely occur. FP-Growth instead lists the pairs and triples
that actually appear together often (support). We then keep only those that
co-occur clearly more than chance (lift), because "glycerin + water" is
common simply because both are everywhere and says nothing about formulation.

Mining runs inside each category: skincare and fragrance use different
building blocks, and a pooled run would be dominated by the biggest category.
Mining never looks at the targets, so using all products here does not leak
outcome information into the models.
"""

from itertools import combinations

from mlxtend.frequent_patterns import fpgrowth
import numpy as np
import pandas as pd

MIN_SUPPORT = 0.05       # in at least 5% of the category's products
MIN_LIFT = 1.5           # together at least 1.5x more often than by chance
MAX_LEN = 3
MAX_PER_CATEGORY = 30    # otherwise fragrance allergen clusters fill the whole list
MIN_CATEGORY_SIZE = 300

# Named in the synopsis (section 1.4 / 2.6.3) before any data was looked at, so
# they are always tested and reported as confirmatory, whatever their lift.
PRESPECIFIED = [
    ("glycerin", "sodium hyaluronate"),
    ("glycerin", "hyaluronic acid"),
    ("niacinamide", "zinc pca"),
]


def _lift(itemset, support, single_support):
    return support / np.prod([single_support[i] for i in itemset])


def mine_combinations(frame, ingredient_cols, category_col="primary_category"):
    """Return a table of combinations: items, category, support, lift."""
    rows = []
    for cat, sub in frame.groupby(category_col):
        if len(sub) < MIN_CATEGORY_SIZE:
            continue
        basket = sub[ingredient_cols].astype(bool)
        basket = basket.loc[:, basket.mean() >= MIN_SUPPORT]
        if basket.shape[1] < 2:
            continue
        found = fpgrowth(basket, min_support=MIN_SUPPORT, use_colnames=True, max_len=MAX_LEN)
        single = basket.mean()
        for items, support in zip(found.itemsets, found.support):
            if len(items) < 2:
                continue
            items = tuple(sorted(i[len("ing__"):] for i in items))
            lift = _lift([f"ing__{i}" for i in items], support, single)
            if lift >= MIN_LIFT:
                rows.append({"items": items, "category": cat, "support": support, "lift": lift,
                             "prespecified": False})
    table = pd.DataFrame(rows, columns=["items", "category", "support", "lift", "prespecified"])
    if not table.empty:
        table = _drop_redundant_triples(table)
        table = (table.sort_values(["category", "support", "lift"], ascending=False)
                 .groupby("category").head(MAX_PER_CATEGORY))
        # the same item set can be frequent in two categories: keep one column for it
        table = table.drop_duplicates("items")
        table["prespecified"] = table["items"].isin({tuple(sorted(p)) for p in PRESPECIFIED})
    return pd.concat([table, _prespecified(frame, table)], ignore_index=True)


def _prespecified(frame, mined):
    rows = []
    known = set(mined["items"])
    for items in PRESPECIFIED:
        items = tuple(sorted(items))
        cols = [f"ing__{i}" for i in items]
        if items in known or not all(c in frame for c in cols):
            continue
        together = frame[cols].all(axis=1).mean()
        rows.append({"items": items, "category": "All", "support": together,
                     "lift": _lift(cols, together, frame[cols].mean()) if together else 0.0,
                     "prespecified": True})
    return pd.DataFrame(rows, columns=["items", "category", "support", "lift", "prespecified"])


def untestable_prespecified(frame):
    """Pre-specified combinations whose ingredients are too rare to have a feature column."""
    return [" + ".join(p) for p in PRESPECIFIED if not all(f"ing__{i}" in frame for i in p)]


def _drop_redundant_triples(table):
    pairs = {t for t in table["items"] if len(t) == 2}
    keep = [len(t) == 2 or not all(p in pairs for p in combinations(t, 2)) for t in table["items"]]
    return table[keep]


def combo_column(items):
    return "combo__" + " + ".join(items)


def add_combo_features(frame, combos):
    """One 0/1 column per combination: does the product contain all its ingredients?"""
    cols = {}
    for items in combos["items"]:
        cols[combo_column(items)] = frame[[f"ing__{i}" for i in items]].all(axis=1).astype(np.int8)
    added = pd.DataFrame(cols, index=frame.index)
    return pd.concat([frame, added], axis=1), list(added.columns)
