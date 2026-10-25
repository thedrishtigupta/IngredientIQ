"""Robustness checks: do the main conclusions survive other reasonable choices?

1. Ablation: which ingredient feature family (if any) carries signal? Model A
   plus only individual ingredients / only functional groups / only
   combinations, and ingredients with no metadata at all. "ingredients_only"
   shows how much success ingredient lists predict on their own; comparing it
   with Model B shows whether that is new information or metadata in disguise.
2. Per-category models: the main run models All and Skincare; here Makeup,
   Hair and Fragrance get their own Model A vs B comparison.
3. Sensitivity: rebuild the dataset with the review threshold at 10 and 50
   instead of 25, and without family deduplication, then rerun the tests and
   the LightGBM comparison.

LightGBM only (the strongest model in the main run) to keep this under ~45 min.
"""

import pandas as pd

from research import models
from research.combos import add_combo_features, mine_combinations
from research.dataset import build_study_data
from research.stats import ALPHA, association_tests, bh

ABLATION_VARIANTS = ("A+ingredients", "A+functional", "A+combinations", "ingredients_only")
CATEGORY_SCOPES = ["Makeup", "Hair", "Fragrance"]
SENSITIVITY = {
    "reviews >= 10": {"min_reviews": 10},
    "reviews >= 50": {"min_reviews": 50},
    "no deduplication": {"dedup": False},
}
MODEL = "LightGBM"
# Not part of the ablation question: B is the main comparison, ingredients_only a reference point
NOT_TESTED = {"B", "ingredients_only"}


def with_fdr(comp, family=None, exclude=()):
    """Add q_corrected: Benjamini-Hochberg over the corrected p-values of one family.

    Dozens of comparisons are run per check, so a few nominal p < 0.05 are
    expected by chance alone; only q < 0.05 is reported as a finding.
    `family` names a column whose values are separate families (e.g. setting);
    rows whose variant is in `exclude` are not tested and get no q.
    """
    comp = comp.copy()
    comp["q_corrected"] = float("nan")
    tested = comp[~comp.variant.isin(exclude)]
    groups = tested.groupby(family).groups.values() if family else [tested.index]
    for idx in groups:
        comp.loc[idx, "q_corrected"] = bh(comp.loc[idx, "p_corrected"])
    return comp


def ablation(study, main_folds, log=print):
    """Ablation variants on the main run's folds, plus its A and B scores for reference."""
    new = models.cross_validate(study, cvs=("random",), model_names=[MODEL],
                                variants=ABLATION_VARIANTS, log=log)
    main = main_folds[(main_folds.model == MODEL) & (main_folds.cv == "random")]
    return with_fdr(models.compare(pd.concat([main, new], ignore_index=True)), exclude=NOT_TESTED)


def per_category(study, log=print):
    folds = models.cross_validate(study, scopes=CATEGORY_SCOPES, model_names=[MODEL], log=log)
    return with_fdr(models.compare(folds))


def _with_combos(study):
    combos = mine_combinations(study.frame, study.ingredient_cols)
    study.frame, study.combo_cols = add_combo_features(study.frame, combos)
    return study, combos


def sensitivity(sources, log=print):
    """(test summary, model comparison) for every alternative setting."""
    tests, comparisons = [], []
    repeats = models.REPEATS
    models.REPEATS = 1  # 5 folds per setting is enough to see whether the verdict flips
    try:
        for name, options in SENSITIVITY.items():
            log(f"  setting: {name}")
            study, combos = _with_combos(build_study_data(sources, **options))
            assoc = association_tests(study, combos)
            summary = (assoc.groupby(["scope", "target"])
                       .agg(tests=("feature", "size"),
                            significant_raw=("q_raw", lambda q: int((q < ALPHA).sum())),
                            significant_adjusted=("q_adj", lambda q: int((q < ALPHA).sum())),
                            robust=("robust", "sum"))
                       .reset_index())
            pre = assoc[assoc.prespecified & (assoc.scope == "All")]
            for r in pre.itertuples():
                summary.loc[len(summary)] = {"scope": "prespecified", "target": f"{r.target}: {r.feature}",
                                             "tests": 1, "significant_raw": int(r.q_raw < ALPHA),
                                             "significant_adjusted": int(r.q_adj < ALPHA),
                                             "robust": int(r.robust)}
            tests.append(summary.assign(setting=name, products=len(study.frame)))
            comp = models.compare(models.cross_validate(study, cvs=("random",), model_names=[MODEL], log=log))
            comparisons.append(comp.assign(setting=name, products=len(study.frame)))
    finally:
        models.REPEATS = repeats
    return pd.concat(tests, ignore_index=True), with_fdr(pd.concat(comparisons, ignore_index=True), "setting")
