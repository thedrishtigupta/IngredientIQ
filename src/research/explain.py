"""Step 6: which features does the ingredient-aware model (Model B) lean on?

A LightGBM Model B is trained on all products of a scope, then SHAP splits
every single prediction into "how much did each feature push it up or down".
Averaging the absolute pushes gives a global importance per feature.

Two summaries come out of it:
- importance per feature, with a direction (does having more of it push the
  prediction up or down?);
- the share of all SHAP importance that goes to ingredient features versus
  baseline metadata: how much of the model's reasoning is about ingredients.

Every ingredient feature in the top list is then cross-checked against the
statistical tests of step 3: is the same ingredient also significant there
after adjusting for brand, and in the same direction? A SHAP-important
ingredient that fails that check is the model exploiting something the
statistics cannot confirm, and is reported as such.
"""

import numpy as np
import pandas as pd
import shap

from research.dataset import TARGETS, pretty_feature
from research.models import feature_columns, make_models, make_pipeline
from research.stats import scope_rows

TOP_N = 20


def feature_group(name):
    """Pipeline column name -> which family of features it belongs to."""
    col = name.split("__", 1)[1] if name.startswith(("num__", "cat__")) else name
    if col.startswith(("ing__", "pos__")) or col == "n_ingredients":
        return "ingredient"
    if col.startswith("combo__"):
        return "combination"
    if col.startswith("fg__"):
        return "functional_group"
    return "baseline"


def _source_column(name):
    """Pipeline name -> study column (position features map to their ingredient)."""
    col = name.split("__", 1)[1] if name.startswith(("num__", "cat__")) else name
    return "ing__" + col[5:] if col.startswith("pos__") else col


def shap_for_target(study, target, scope="All"):
    task = TARGETS[target][0]
    sub = scope_rows(study.frame, scope)
    sub = sub[sub[target].notna()]
    cat, num = feature_columns(study, target, "B")
    model, scale = make_models(task)["LightGBM"]
    pipe = make_pipeline(model, scale, cat, num).fit(sub[cat + num], sub[target])
    x = pipe["pre"].transform(sub[cat + num])
    names = pipe["pre"].get_feature_names_out()

    values = shap.TreeExplainer(pipe["model"]).shap_values(x)
    if isinstance(values, list):       # older shap: one array per class
        values = values[1]
    if values.ndim == 3:
        values = values[:, :, 1]

    mean_abs = np.abs(values).mean(axis=0)
    direction = []
    for j in range(x.shape[1]):
        col = x[:, j]
        if col.std() == 0 or values[:, j].std() == 0:
            direction.append(0.0)
        else:
            direction.append(float(np.corrcoef(col, values[:, j])[0, 1]))
    return pd.DataFrame({
        "scope": scope, "target": target, "column": names,
        "feature": [pretty_feature(n) for n in names],
        "group": [feature_group(n) for n in names],
        "mean_abs_shap": mean_abs,
        "direction": np.where(np.array(direction) >= 0, "positive", "negative"),
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)


def cross_check(importance, assoc):
    """Attach the step-3 adjusted test result to every ingredient-type feature."""
    lookup = assoc.set_index(["scope", "target", "feature"])
    q, beta, robust, agrees = [], [], [], []
    for r in importance.itertuples():
        key = (r.scope, r.target, _source_column(r.column))
        if r.group in ("ingredient", "combination") and key in lookup.index:
            a = lookup.loc[key]
            q.append(a.q_adj)
            beta.append(a.adj_beta)
            robust.append(bool(a.robust))
            agrees.append(bool(np.sign(a.adj_beta) == (1 if r.direction == "positive" else -1)))
        else:
            q.append(np.nan); beta.append(np.nan); robust.append(None); agrees.append(None)
    return importance.assign(stats_q_adj=q, stats_adj_beta=beta, stats_robust=robust,
                             direction_agrees=agrees)


def explain(study, assoc, scopes=("All", "Skincare"), log=print):
    """Importance tables for every scope x target, plus group shares."""
    tables = []
    for scope in scopes:
        for target in TARGETS:
            rows = scope_rows(study.frame, scope)
            if rows[target].notna().sum() < 200:
                continue
            if scope == "All" and rows.loc[rows[target].notna(), "primary_category"].nunique() == 1:
                continue
            log(f"  SHAP {scope:9} {target}")
            tables.append(cross_check(shap_for_target(study, target, scope), assoc))
    importance = pd.concat(tables, ignore_index=True)
    shares = (importance.groupby(["scope", "target", "group"]).mean_abs_shap.sum()
              / importance.groupby(["scope", "target"]).mean_abs_shap.sum()).rename("share").reset_index()
    return importance, shares
