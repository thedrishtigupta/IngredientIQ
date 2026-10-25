"""Turn the step 3-6 tables into results.json (for the web page) and a Markdown report.

Nothing here computes new statistics; it only selects and formats what the
other steps produced, so the page and the report can never disagree with
the CSV files they came from.
"""

from datetime import date
import math

import numpy as np
import pandas as pd

from research.dataset import TARGETS, pretty_feature
from research.stats import ALPHA, scope_rows

METRIC_LABELS = {
    "r2": ("R²", True), "mae": ("MAE", False), "rmse": ("RMSE", False),
    "accuracy": ("Accuracy", True), "precision": ("Precision", True), "recall": ("Recall", True),
    "f1": ("F1", True), "roc_auc": ("ROC-AUC", True),
}
REG_METRICS = ["r2", "mae", "rmse"]
CLF_METRICS = ["accuracy", "precision", "recall", "f1", "roc_auc"]
HEADLINE_MODEL = "LightGBM"
TOP = 15


def _clean(v):
    """JSON-safe: numpy -> python, NaN -> None."""
    if isinstance(v, (np.floating, float)):
        return None if math.isnan(v) else round(float(v), 4)
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.bool_):
        return bool(v)
    return v


def _records(df):
    return [{k: _clean(v) for k, v in row.items()} for row in df.to_dict("records")]


def _metrics(task):
    return REG_METRICS if task == "regression" else CLF_METRICS


def _metric_rows(row, task):
    return [{"metric": METRIC_LABELS[m][0], "modelA": _clean(row[f"A_{m}"]), "modelB": _clean(row[f"B_{m}"]),
             "higherIsBetter": METRIC_LABELS[m][1]} for m in _metrics(task)]


def _verdict(gain, p):
    if p is None or (isinstance(p, float) and math.isnan(p)) or p >= ALPHA:
        return "no significant difference"
    return "B better" if gain > 0 else "A better"


def build_results(study, untestable, assoc, fg, comparison, importance, shares):
    scopes = {}
    for scope in sorted(set(comparison.scope), key=lambda s: s != "All"):
        targets = {}
        for target, (task, label) in TARGETS.items():
            comp = comparison[(comparison.scope == scope) & (comparison.target == target)]
            if comp.empty:
                continue
            a = assoc[(assoc.scope == scope) & (assoc.target == target)]
            imp = importance[(importance.scope == scope) & (importance.target == target)]
            sh = shares[(shares.scope == scope) & (shares.target == target)]
            head = comp[(comp.model == HEADLINE_MODEL) & (comp.cv == "random")].iloc[0]

            robust = a[a.robust].assign(abs_beta=lambda d: d.adj_beta.abs()).sort_values("abs_beta", ascending=False)
            targets[target] = {
                "label": label, "task": task, "n": int(scope_rows(study.frame, scope)[target].notna().sum()),
                "modelComparison": _metric_rows(head, task),
                "comparisons": [{
                    "model": r.model, "cv": r.cv, "metric": METRIC_LABELS[r.primary_metric][0],
                    "a": _clean(getattr(r, f"A_{r.primary_metric}")), "b": _clean(getattr(r, f"B_{r.primary_metric}")),
                    "gain": _clean(r.gain), "pCorrected": _clean(r.p_corrected), "bWins": int(r.b_wins),
                    "folds": int(r.folds), "verdict": _verdict(r.gain, r.p_corrected),
                } for r in comp.itertuples()],
                "tests": {"total": len(a), "significantRaw": int((a.q_raw < ALPHA).sum()),
                          "significantAdjusted": int((a.q_adj < ALPHA).sum()), "robust": int(a.robust.sum())},
                "associations": [{"label": pretty_feature(r.feature), "kind": r.kind,
                                  "effect": _clean(r.adj_beta), "rawEffect": _clean(r.effect),
                                  "adjustedP": _clean(r.q_adj), "nWith": int(r.n_with)}
                                 for r in robust.head(TOP).itertuples()],
                "shap": [{"feature": r.feature, "meanAbsShap": _clean(r.mean_abs_shap), "direction": r.direction,
                          "group": r.group} for r in imp.head(TOP).itertuples()],
                "ingredientShap": [{"feature": r.feature, "meanAbsShap": _clean(r.mean_abs_shap),
                                    "direction": r.direction, "group": r.group,
                                    "statsQ": _clean(r.stats_q_adj),
                                    # None = no adjusted test exists for this feature (functional groups)
                                    "confirmed": None if r.stats_robust is None
                                    else bool(r.stats_robust) and bool(r.direction_agrees)}
                                   for r in imp[imp.group != "baseline"].head(TOP).itertuples()],
                "shapShares": {r.group: _clean(r.share) for r in sh.itertuples()},
            }
        scopes[scope] = targets

    pre = assoc[assoc.prespecified & (assoc.scope.isin(["All", "Skincare"]))]
    return {
        "state": "ready",
        "generatedOn": date.today().isoformat(),
        "dataset": {**{k: _clean(v) for k, v in study.notes.items() if k != "targets_available"},
                    "targetsAvailable": study.notes["targets_available"],
                    "categories": study.frame.primary_category.value_counts().to_dict(),
                    "ingredientFeatures": len(study.ingredient_feature_cols),
                    "combinations": len(study.combo_cols)},
        "prespecified": [{"label": pretty_feature(r.feature), "scope": r.scope, "target": r.target,
                          "effect": _clean(r.adj_beta), "adjustedP": _clean(r.q_adj), "rawP": _clean(r.p_raw)}
                         for r in pre.itertuples()],
        "untestable": untestable,
        "scopes": scopes,
    }


def _table(df, cols, headers=None, fmt=None):
    fmt = fmt or {}
    lines = ["| " + " | ".join(headers or cols) + " |", "|" + "---|" * len(cols)]
    for row in df[cols].itertuples(index=False):
        cells = []
        for c, v in zip(cols, row):
            if c in fmt:
                cells.append(fmt[c](v))
            elif isinstance(v, float):
                cells.append("" if math.isnan(v) else f"{v:.3f}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _p(v):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return "<0.001" if v < 0.001 else f"{v:.3f}"


def write_markdown(path, results, assoc, fg, comparison, importance, shares):
    n = results["dataset"]
    out = [
        "# Research results: do ingredients predict product success?",
        "",
        f"*Generated by `scripts/run_research.py` on {results['generatedOn']}. Do not edit by hand —"
        " re-run the script. Method and interpretation: [RESEARCH.md](RESEARCH.md).*",
        "",
        "All findings are associations in this Sephora dataset. None is a causal, medical or safety claim.",
        "",
        "## 1. Data",
        "",
        f"- Catalogue products: {n['catalogue_products']:,}",
        f"- Without an ingredient list: {n['no_ingredients']:,}; multi-component kits: {n['multi_component_kits']:,}",
        f"- In scope (single formula, no sets/minis/tools): {n['in_scope_before_dedup']:,}",
        f"- After keeping one product per family (minis, re-listings, identical formulas): **{n['analysis_products']:,}**",
        f"- Ingredient features in Model B: {n['ingredientFeatures']} (incl. {n['combinations']} combinations)",
        "",
        _table(pd.DataFrame([{"target": TARGETS[t][1], "products": v} for t, v in n["targetsAvailable"].items()]),
               ["target", "products"]),
        "",
        "## 2. Model A (metadata) vs Model B (+ ingredients)",
        "",
        "Primary metric: R² (regression) or ROC-AUC (classification). `gain` = B − A averaged over folds;"
        " `p (corr.)` = Nadeau–Bengio corrected paired t-test. *random* = repeated 5-fold CV;"
        " *unseen_brand* = whole brands held out.",
        "",
    ]
    comp = comparison.copy()
    comp["metric"] = comp.primary_metric.map(lambda m: METRIC_LABELS[m][0])
    comp["A"] = [getattr(r, f"A_{r.primary_metric}") for r in comp.itertuples()]
    comp["B"] = [getattr(r, f"B_{r.primary_metric}") for r in comp.itertuples()]
    comp["wins"] = comp.b_wins.astype(str) + "/" + comp.folds.astype(str)
    comp["verdict"] = [_verdict(g, p) for g, p in zip(comp.gain, comp.p_corrected)]
    comp["target"] = comp.target.map(lambda t: TARGETS[t][1])
    out += [_table(comp, ["scope", "target", "cv", "model", "metric", "A", "B", "gain", "wins", "p_corrected", "verdict"],
                   ["scope", "target", "CV", "model", "metric", "A", "B", "gain", "B wins", "p (corr.)", "verdict"],
                   fmt={"p_corrected": _p, "gain": lambda v: f"{v:+.3f}"}), ""]

    out += ["### All metrics (LightGBM, random CV)", ""]
    for scope, targets in results["scopes"].items():
        for t, r in targets.items():
            df = pd.DataFrame(r["modelComparison"])
            out += [f"**{scope} — {r['label']}** (n = {r['n']:,})", "",
                    _table(df, ["metric", "modelA", "modelB"], ["metric", "Model A", "Model B"]), ""]

    out += ["## 3. Association tests", "",
            "q = Benjamini–Hochberg corrected p within each scope × target. *Adjusted* = brand, subcategory"
            " and log price held fixed. *Robust* = raw and adjusted q < 0.05 with the same sign.", ""]
    summary = (assoc.groupby(["scope", "target"])
               .agg(tests=("feature", "size"), raw=("q_raw", lambda q: int((q < ALPHA).sum())),
                    adjusted=("q_adj", lambda q: int((q < ALPHA).sum())), robust=("robust", "sum"))
               .reset_index())
    summary["target"] = summary.target.map(lambda t: TARGETS[t][1])
    out += [_table(summary, ["scope", "target", "tests", "raw", "adjusted", "robust"],
                   ["scope", "target", "tests", "q<0.05 raw", "q<0.05 adjusted", "robust"]), ""]

    out += ["### Robust associations (largest adjusted effects)", "",
            "`adj β` = difference in the outcome, in standard deviations (probability for high performer),"
            " between otherwise comparable products with and without the feature. `raw effect` = Cliff's δ"
            " (rate difference for high performer).", ""]
    rob = assoc[assoc.robust].assign(abs_beta=lambda d: d.adj_beta.abs())
    rob = rob.sort_values(["scope", "target", "abs_beta"], ascending=[True, True, False]).groupby(["scope", "target"]).head(8)
    rob = rob.assign(feature=rob.feature.map(pretty_feature), target=rob.target.map(lambda t: TARGETS[t][1]))
    out += [_table(rob, ["scope", "target", "feature", "kind", "n_with", "effect", "adj_beta", "q_adj"],
                   ["scope", "target", "feature", "kind", "n with", "raw effect", "adj β", "q adj"],
                   fmt={"q_adj": _p, "adj_beta": lambda v: f"{v:+.3f}", "effect": lambda v: f"{v:+.3f}"}), ""]

    out += ["### Pre-specified hypotheses (from the synopsis)", ""]
    pre = assoc[assoc.prespecified].assign(feature=lambda d: d.feature.map(pretty_feature),
                                           target=lambda d: d.target.map(lambda t: TARGETS[t][1]))
    out += [_table(pre, ["scope", "target", "feature", "n_with", "effect", "p_raw", "adj_beta", "p_adj", "q_adj"],
                   ["scope", "target", "combination", "n with", "raw effect", "p raw", "adj β", "p adj", "q adj"],
                   fmt={"p_raw": _p, "p_adj": _p, "q_adj": _p}), ""]
    if results["untestable"]:
        out += [f"Not testable (ingredient too rare for a feature column): {', '.join(results['untestable'])}.", ""]

    out += ["### Functional groups (Kruskal–Wallis, none / low / high share)", ""]
    f = fg[fg.q_raw < ALPHA].sort_values("epsilon_sq", ascending=False).head(25)
    f = f.assign(feature=f.feature.map(pretty_feature), target=f.target.map(lambda t: TARGETS[t][1]))
    out += [_table(f, ["scope", "target", "feature", "mean_none", "mean_low", "mean_high", "epsilon_sq", "q_raw"],
                   ["scope", "target", "group", "mean none", "mean low", "mean high", "ε²", "q"],
                   fmt={"q_raw": _p}), "",
            "Not adjusted for brand; read together with the adjusted ingredient tests above.", ""]

    out += ["## 4. SHAP (LightGBM Model B, trained on all products of the scope)", "",
            "### Share of total |SHAP| by feature family", ""]
    sh = shares.pivot_table(index=["scope", "target"], columns="group", values="share").reset_index().fillna(0)
    sh["target"] = sh.target.map(lambda t: TARGETS[t][1])
    groups = [g for g in ["baseline", "ingredient", "functional_group", "combination"] if g in sh]
    out += [_table(sh, ["scope", "target"] + groups, fmt={g: (lambda v: f"{v:.1%}") for g in groups}), ""]

    out += ["### Top ingredient-type features and their statistical cross-check", "",
            "`confirmed` = the same feature is a robust association in section 3 with the same direction.", ""]
    imp = importance[importance.group != "baseline"].groupby(["scope", "target"]).head(10).copy()
    imp["confirmed"] = [("yes" if r and a else "no") if r is not None else "n/a"
                        for r, a in zip(imp.stats_robust, imp.direction_agrees)]
    imp["target"] = imp.target.map(lambda t: TARGETS[t][1])
    out += [_table(imp, ["scope", "target", "feature", "group", "mean_abs_shap", "direction", "stats_q_adj", "confirmed"],
                   ["scope", "target", "feature", "family", "mean abs SHAP", "direction", "q adj", "confirmed"],
                   fmt={"stats_q_adj": _p, "mean_abs_shap": lambda v: f"{v:.4f}"}), ""]

    out += ["### Top 15 features overall", ""]
    top = importance.groupby(["scope", "target"]).head(15).assign(target=lambda d: d.target.map(lambda t: TARGETS[t][1]))
    out += [_table(top, ["scope", "target", "feature", "group", "mean_abs_shap", "direction"],
                   fmt={"mean_abs_shap": lambda v: f"{v:.4f}"}), ""]
    path.write_text("\n".join(out), encoding="utf-8")
