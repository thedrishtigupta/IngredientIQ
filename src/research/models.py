"""Step 5: does adding ingredient features improve prediction of success?

Model A sees only what a shop already knows without reading the label: brand,
category, price, flags (new, exclusive, ...) and, where it is not circular,
existing popularity. Model B sees exactly the same plus every ingredient
feature (presence, position, functional-group shares, combinations).
Both are trained on identical folds, so the only difference is the features.

Two ways of splitting the data:
- "random": repeated 5-fold cross-validation. Answers "does B predict better?"
- "unseen_brand": every fold holds out whole brands. The model must predict
  products of brands it never saw, so it cannot lean on "brand X is popular".
  If ingredients carry real signal, B's advantage should show up here too.

Fold scores are not independent (folds share training data), so a plain
paired t-test is too optimistic. We report it, but judge with the
Nadeau-Bengio corrected t-test, which inflates the variance accordingly.
"""

import time

from lightgbm import LGBMClassifier, LGBMRegressor
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegressionCV, RidgeCV
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error, precision_score,
                             r2_score, recall_score, roc_auc_score, root_mean_squared_error)
from sklearn.model_selection import GroupKFold, RepeatedKFold, RepeatedStratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from research.dataset import BASE_CATEGORICAL, BASE_NUMERIC, POPULARITY_CONTROLS, TARGETS
from research.stats import scope_rows

SEED = 42
FOLDS = 5
REPEATS = 3
MODEL_SCOPES = ["All", "Skincare"]
PRIMARY_METRIC = {"regression": "r2", "classification": "roc_auc"}


def make_models(task):
    """Fresh, untrained models: an interpretable baseline and two tree ensembles.

    The linear models pick their own regularisation by inner cross-validation.
    With one fixed strength, Model B (hundreds more columns) would be
    under-regularised and lose for that reason alone, not for lack of signal.
    """
    if task == "regression":
        return {
            "Ridge": (RidgeCV(alphas=np.logspace(-1, 4, 11)), True),
            "Random Forest": (RandomForestRegressor(
                n_estimators=200, min_samples_leaf=3, max_features=0.2, n_jobs=-1, random_state=SEED), False),
            "LightGBM": (LGBMRegressor(
                n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=20,
                subsample=0.8, subsample_freq=1, colsample_bytree=0.5, random_state=SEED, verbose=-1), False),
        }
    return {
        "Logistic Regression": (LogisticRegressionCV(
            Cs=np.logspace(-3, 1, 6), cv=3, scoring="roc_auc", max_iter=3000, class_weight="balanced"), True),
        "Random Forest": (RandomForestClassifier(
            n_estimators=200, min_samples_leaf=3, max_features=0.2, class_weight="balanced",
            n_jobs=-1, random_state=SEED), False),
        "LightGBM": (LGBMClassifier(
            n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=20,
            subsample=0.8, subsample_freq=1, colsample_bytree=0.5, class_weight="balanced",
            random_state=SEED, verbose=-1), False),
    }


# variant -> (uses Model A's metadata?, ingredient feature families added)
# A and B are the main comparison; the others are the ablation of the robustness step.
VARIANTS = {
    "A": (True, []),
    "B": (True, ["ingredient", "functional", "combination"]),
    "A+ingredients": (True, ["ingredient"]),
    "A+functional": (True, ["functional"]),
    "A+combinations": (True, ["combination"]),
    "ingredients_only": (False, ["ingredient", "functional", "combination"]),
}


def feature_columns(study, target, variant):
    """(categorical, numeric) columns for a model variant (see VARIANTS)."""
    with_metadata, families = VARIANTS[variant]
    categorical = BASE_CATEGORICAL if with_metadata else []
    numeric = BASE_NUMERIC + POPULARITY_CONTROLS[target] if with_metadata else []
    columns = {
        "ingredient": ["n_ingredients"] + study.ingredient_cols + study.prominence_cols,
        "functional": study.functional_cols,
        "combination": study.combo_cols,
    }
    for family in families:
        numeric = numeric + columns[family]
    return categorical, numeric


def make_pipeline(model, scale, categorical, numeric):
    pre = ColumnTransformer([
        # brands / subcategories with < 10 products share one "rare" column
        ("cat", OneHotEncoder(min_frequency=10, handle_unknown="infrequent_if_exist",
                              sparse_output=False, dtype=np.float32), categorical),
        ("num", StandardScaler() if scale else "passthrough", numeric),
    ])
    return Pipeline([("pre", pre), ("model", model)])


def splits(sub, task, cv):
    y = sub["_y"].to_numpy()
    if cv == "random":
        splitter = (RepeatedStratifiedKFold if task == "classification" else RepeatedKFold)(
            n_splits=FOLDS, n_repeats=REPEATS, random_state=SEED)
        return list(splitter.split(sub, y))
    return list(GroupKFold(n_splits=FOLDS, shuffle=True, random_state=SEED).split(sub, y, sub.brand_name))


def score(task, y_true, model, x):
    if task == "regression":
        pred = model.predict(x)
        return {"r2": r2_score(y_true, pred), "mae": mean_absolute_error(y_true, pred),
                "rmse": root_mean_squared_error(y_true, pred)}
    proba = model.predict_proba(x)[:, 1]
    pred = (proba >= 0.5).astype(int)
    return {"accuracy": accuracy_score(y_true, pred),
            "precision": precision_score(y_true, pred, zero_division=0),
            "recall": recall_score(y_true, pred), "f1": f1_score(y_true, pred),
            "roc_auc": roc_auc_score(y_true, proba)}


def cross_validate(study, scopes=MODEL_SCOPES, targets=None, cvs=("random", "unseen_brand"),
                   model_names=None, variants=("A", "B"), log=print):
    """Fold-level scores for every scope x target x split x model x variant."""
    rows = []
    for scope in scopes:
        base = scope_rows(study.frame, scope)
        for target in targets or TARGETS:
            task = TARGETS[target][0]
            sub = base[base[target].notna()].assign(_y=lambda d: d[target]).reset_index(drop=True)
            if len(sub) < 200:
                continue
            if scope == "All" and sub.primary_category.nunique() == 1:
                continue  # e.g. rec_rate: every product with one is Skincare -> same run twice
            for cv in cvs:
                folds = splits(sub, task, cv)
                for name, (model, scale) in make_models(task).items():
                    if model_names and name not in model_names:
                        continue
                    started = time.time()
                    for variant in variants:
                        cat, num = feature_columns(study, target, variant)
                        x = sub[cat + num]
                        for i, (tr, te) in enumerate(folds):
                            m = make_models(task)[name][0]
                            pipe = make_pipeline(m, scale, cat, num).fit(x.iloc[tr], sub._y.iloc[tr])
                            rows.append({"scope": scope, "target": target, "task": task, "cv": cv,
                                         "model": name, "variant": variant, "fold": i,
                                         "n_train": len(tr), "n_test": len(te),
                                         **score(task, sub._y.iloc[te].to_numpy(), pipe, x.iloc[te])})
                    log(f"  {scope:9} {target:15} {cv:13} {name:20} {time.time() - started:6.1f}s")
    return pd.DataFrame(rows)


def corrected_ttest(diffs, n_train, n_test):
    """Nadeau & Bengio (2003): paired t-test corrected for overlapping training sets."""
    d = np.asarray(diffs, dtype=float)
    k = len(d)
    var = d.var(ddof=1)
    if var == 0:
        return float("nan")
    t = d.mean() / np.sqrt((1 / k + n_test / n_train) * var)
    return float(2 * stats.t.sf(abs(t), k - 1))


def compare(folds, baseline="A"):
    """One row per scope x target x split x model x variant: variant vs baseline.

    Columns A_<metric> hold the baseline, B_<metric> the compared variant
    (Model B in the main comparison, an ablation variant otherwise).
    """
    out = []
    keys = ["scope", "target", "task", "cv", "model"]
    for key, g in folds.groupby(keys, sort=False):
        a = g[g.variant == baseline].sort_values("fold")
        task = key[2]
        primary = PRIMARY_METRIC[task]
        metrics = ["r2", "mae", "rmse"] if task == "regression" else ["accuracy", "precision", "recall", "f1", "roc_auc"]
        for variant in [v for v in g.variant.unique() if v != baseline]:
            b = g[g.variant == variant].sort_values("fold")
            row = {**dict(zip(keys, key)), "variant": variant}
            for m in metrics:
                row[f"A_{m}"] = a[m].mean()
                row[f"B_{m}"] = b[m].mean()
            diffs = b[primary].to_numpy() - a[primary].to_numpy()
            row.update({
                "primary_metric": primary,
                "gain": diffs.mean(), "gain_sd": diffs.std(ddof=1),
                "b_wins": int((diffs > 0).sum()), "folds": len(diffs),
                "p_paired": float(stats.ttest_rel(b[primary], a[primary]).pvalue),
                "p_corrected": corrected_ttest(diffs, a.n_train.mean(), a.n_test.mean()),
            })
            out.append(row)
    return pd.DataFrame(out)
