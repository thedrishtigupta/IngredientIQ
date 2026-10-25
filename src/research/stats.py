"""Step 3: which ingredients / combinations go with more successful products?

For every (scope, target, feature) we run two kinds of test:

1. Raw group comparison, as in the synopsis:
   - continuous target (rating, loves, ...): Mann-Whitney U between products
     with and without the feature, effect size = Cliff's delta (and Cohen's d);
     for ingredients also a "dose" Spearman: among products that contain it,
     does sitting higher in the list go with a better outcome?
   - high_performer label: chi-square, effect size = Cramer's V.
   - functional groups (share of humectants, ...): Kruskal-Wallis across
     none / low / high, effect size = epsilon squared.

2. Adjusted test: the same question after removing brand, subcategory and
   price (a regression with those as controls). Raw tests alone are easily
   fooled: if one popular brand puts squalane in everything, squalane looks
   "successful". The adjusted test asks whether the ingredient still matters
   when comparing products of the same brand and type at the same price.

Thousands of tests are run, so p-values are corrected with Benjamini-Hochberg
(false discovery rate) within each (scope, target) family; the corrected
value is called q. A finding is called *robust* only if both the raw and the
adjusted test have q < 0.05 and point the same way.

Everything here is association in this dataset, never cause.
"""

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

from research.dataset import TARGETS

ALPHA = 0.05
MIN_GROUP = 30           # both "with" and "without" need at least this many products
MIN_SCOPE_SIZE = 300
ADJUST_FOR = ["brand_name", "secondary_category"]


def scopes(frame):
    """All products, plus each category large enough to test on its own."""
    sizes = frame.primary_category.value_counts()
    return ["All"] + [c for c in sizes.index if sizes[c] >= MIN_SCOPE_SIZE]


def scope_rows(frame, scope):
    return frame if scope == "All" else frame[frame.primary_category == scope]


def cliffs_delta_from_u(u, n1, n2):
    """Cliff's delta: P(with > without) - P(with < without), from -1 to 1."""
    return 2 * u / (n1 * n2) - 1


def cohens_d(a, b):
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return (a.mean() - b.mean()) / pooled if pooled > 0 else 0.0


def bh(p):
    """Benjamini-Hochberg q-values; NaN stays NaN."""
    p = np.asarray(p, dtype=float)
    q = np.full_like(p, np.nan)
    ok = ~np.isnan(p)
    if ok.any():
        q[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return q


def adjusted_effects(sub, y, features):
    """Effect of each feature on y with brand, subcategory and log price held fixed.

    Uses the Frisch-Waugh-Lovell shortcut: remove the controls from y and
    from every feature once, then each feature's coefficient is a simple
    regression of the leftovers. Same answer as one big regression per
    feature, hundreds of times faster. y is scaled to standard deviations,
    so beta = change in outcome (in SDs) for having the feature.
    """
    controls = pd.get_dummies(sub[ADJUST_FOR], drop_first=True, dtype=float)
    controls["log_price"] = sub["log_price"]
    controls["const"] = 1.0
    c = controls.to_numpy()
    x = sub[features].to_numpy(dtype=float)
    yv = y.to_numpy(dtype=float)
    yv = (yv - yv.mean()) / (yv.std() or 1.0)

    coef, *_ = np.linalg.lstsq(c, np.column_stack([yv, x]), rcond=None)
    resid = np.column_stack([yv, x]) - c @ coef
    ry, rx = resid[:, 0], resid[:, 1:]
    dof = len(yv) - np.linalg.matrix_rank(c) - 1
    sxx = (rx ** 2).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        beta = (rx * ry[:, None]).sum(axis=0) / sxx
        sse = ((ry[:, None] - rx * beta) ** 2).sum(axis=0)
        se = np.sqrt(sse / dof / sxx)
        p = 2 * stats.t.sf(np.abs(beta / se), dof)
    # a feature fully explained by the controls (e.g. only one brand uses it) cannot be tested
    unusable = sxx < 1e-8
    beta[unusable], se[unusable], p[unusable] = np.nan, np.nan, np.nan
    half_width = stats.t.ppf(0.975, dof) * se       # 95% confidence interval
    return beta, se, p, beta - half_width, beta + half_width


def _binary_tests(sub, y, feature, prominence_col, classification):
    has = sub[feature].to_numpy() > 0
    a, b = y[has], y[~has]
    row = {"n_with": int(has.sum()), "n_without": int((~has).sum()),
           "mean_with": float(a.mean()), "mean_without": float(b.mean())}
    if classification:
        table = np.array([[(a == 1).sum(), (a == 0).sum()], [(b == 1).sum(), (b == 0).sum()]])
        chi2, p, *_ = stats.chi2_contingency(table)
        row.update(effect=float(a.mean() - b.mean()), cramers_v=float(np.sqrt(chi2 / len(y))), p_raw=p)
    else:
        u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        row.update(effect=float(cliffs_delta_from_u(u, len(a), len(b))),
                   cohens_d=float(cohens_d(a, b)), p_raw=p)
        dose = sub.loc[has, prominence_col] if prominence_col else None
        # a constant (e.g. always first in the list) has no "dose" to correlate
        if dose is not None and has.sum() >= MIN_GROUP and dose.nunique() > 1 and np.ptp(a) > 0:
            rho, p_dose = stats.spearmanr(dose, a)
            row.update(dose_rho=float(rho), p_dose=float(p_dose))
    return row


def association_tests(study, combos=None):
    """Raw + adjusted tests for every ingredient and combination feature."""
    frame = study.frame
    kinds = {c: "ingredient" for c in study.ingredient_cols}
    kinds.update({c: "combination" for c in study.combo_cols})
    prespecified = set()
    if combos is not None and len(combos):
        prespecified = {"combo__" + " + ".join(i) for i in combos.loc[combos.prespecified, "items"]}
    prominence = set(study.prominence_cols)

    rows = []
    for scope in scopes(frame):
        base = scope_rows(frame, scope)
        for target, (task, _) in TARGETS.items():
            sub = base[base[target].notna()]
            y = sub[target]
            n_has = (sub[list(kinds)] > 0).sum()
            eligible = [f for f in kinds if MIN_GROUP <= n_has[f] <= len(sub) - MIN_GROUP]
            if not eligible:
                continue
            beta, se, p_adj, ci_low, ci_high = adjusted_effects(sub, y, eligible)
            family = []
            for f, b, s, pa, lo, hi in zip(eligible, beta, se, p_adj, ci_low, ci_high):
                pos = "pos__" + f[5:] if f.startswith("ing__") and "pos__" + f[5:] in prominence else None
                row = {"scope": scope, "target": target, "feature": f, "kind": kinds[f],
                       "prespecified": f in prespecified,
                       **_binary_tests(sub, y.to_numpy(), f, pos, task == "classification"),
                       "adj_beta": b, "adj_se": s, "adj_ci_low": lo, "adj_ci_high": hi, "p_adj": pa}
                family.append(row)
            fam = pd.DataFrame(family)
            fam["q_raw"] = bh(fam.p_raw)
            fam["q_adj"] = bh(fam.p_adj)
            if "p_dose" in fam:
                fam["q_dose"] = bh(fam.p_dose)
            rows.append(fam)

    out = pd.concat(rows, ignore_index=True)
    out["robust"] = ((out.q_raw < ALPHA) & (out.q_adj < ALPHA)
                     & (np.sign(out.effect) == np.sign(out.adj_beta)))
    return out


def functional_group_tests(study):
    """Kruskal-Wallis: none / low / high share of each functional group vs each target."""
    frame = study.frame
    rows = []
    for scope in scopes(frame):
        base = scope_rows(frame, scope)
        for target, (task, _) in TARGETS.items():
            sub = base[base[target].notna()]
            family = []
            for f in study.functional_cols:
                share = sub[f]
                positive = share[share > 0]
                if len(positive) < 2 * MIN_GROUP or (share == 0).sum() < MIN_GROUP:
                    continue
                level = np.where(share == 0, "none", np.where(share <= positive.median(), "low", "high"))
                groups = [sub.loc[level == g, target].to_numpy() for g in ("none", "low", "high")]
                h, p = stats.kruskal(*groups)
                n, k = len(sub), 3
                rho, p_rho = stats.spearmanr(share, sub[target])
                family.append({
                    "scope": scope, "target": target, "feature": f, "kind": "functional_group",
                    "mean_none": groups[0].mean(), "mean_low": groups[1].mean(), "mean_high": groups[2].mean(),
                    "kruskal_h": h, "epsilon_sq": max(0.0, (h - k + 1) / (n - k)), "p_raw": p,
                    "spearman_rho": rho, "p_rho": p_rho,
                })
            if family:
                fam = pd.DataFrame(family)
                fam["q_raw"] = bh(fam.p_raw)
                fam["q_rho"] = bh(fam.p_rho)
                rows.append(fam)
    return pd.concat(rows, ignore_index=True)


def summarize(assoc):
    """Per scope and target: how many tests, how many survive each filter."""
    g = assoc.groupby(["scope", "target"])
    return pd.DataFrame({
        "tests": g.size(),
        "significant_raw_q": g.apply(lambda d: int((d.q_raw < ALPHA).sum())),
        "significant_adjusted_q": g.apply(lambda d: int((d.q_adj < ALPHA).sum())),
        "robust": g.robust.sum().astype(int),
    }).reset_index()
