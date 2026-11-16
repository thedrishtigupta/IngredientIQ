"""Figures and LaTeX tables for the research paper, built only from pipeline output.

Reads data/research/*.csv + results.json (from run_research.py and
run_robustness.py) and writes:
    paper/figures/*.pdf  (+ .png previews)   vector, fonts embedded (IEEE PDF eXpress)
    paper/tables/*.tex                        booktabs tables, \\input from the paper
    paper/tables/numbers.tex                  \\newcommand macros for numbers quoted in the text

Nothing is typed by hand: re-run the pipeline, re-run this, rebuild the PDF.
Figures whose input does not exist yet (e.g. robustness not run) are skipped.

Run:  python scripts/make_paper_assets.py
"""

import json
import math
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research.dataset import TARGETS, pretty_feature  # noqa: E402

DATA = ROOT / "data" / "research"
FIG = ROOT / "paper" / "figures"
TAB = ROOT / "paper" / "tables"

# Palette: validated with the dataviz validator on a white surface (light mode).
# Categorical order is the CVD-safety mechanism - do not reorder.
CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
ORDINAL = ["#86b6ef", "#2a78d6", "#104281"]          # raw -> adjusted -> robust
POS, NEG = "#2a78d6", "#e34948"                      # diverging poles
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ONE_COL, TWO_COL = 3.5, 7.16                          # IEEE column widths (inches)

SHORT = {"rating": "Rating", "log_loves": "Loves (log)", "log_reviews": "Reviews (log)",
         "rec_rate": "Recommend rate", "high_performer": "High performer"}
LINEAR = {"Ridge", "Logistic Regression"}


def style():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
        "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "axes.axisbelow": True,
        "pdf.fonttype": 42, "ps.fonttype": 42,          # embed TrueType, not Type 3
        "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "figure.dpi": 150,
    })


def save(fig, name):
    FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG / f"{name}.pdf")
    fig.savefig(FIG / f"{name}.png", dpi=200)
    plt.close(fig)
    print(f"  figure  paper/figures/{name}.pdf")


def row_label(scope, target):
    return f"{scope} · {SHORT[target]}"


def corrected_ci(diffs, n_train, n_test):
    """95% CI of the mean fold difference, Nadeau-Bengio corrected variance."""
    d = np.asarray(diffs, dtype=float)
    k = len(d)
    se = math.sqrt((1 / k + n_test / n_train) * d.var(ddof=1))
    half = stats.t.ppf(0.975, k - 1) * se
    return d.mean(), d.mean() - half, d.mean() + half


def gains(folds, baseline="A", variant="B"):
    """Per scope/target/cv/model: mean gain of `variant` over `baseline` with corrected CI."""
    rows = []
    keys = ["scope", "target", "task", "cv", "model"]
    for key, g in folds.groupby(keys, sort=False):
        a = g[g.variant == baseline].sort_values("fold")
        b = g[g.variant == variant].sort_values("fold")
        if a.empty or b.empty:
            continue
        metric = "r2" if key[2] == "regression" else "roc_auc"
        mean, lo, hi = corrected_ci(b[metric].to_numpy() - a[metric].to_numpy(),
                                    a.n_train.mean(), a.n_test.mean())
        rows.append({**dict(zip(keys, key)), "gain": mean, "lo": lo, "hi": hi})
    return pd.DataFrame(rows)


def ordered_rows(df):
    """Stable row order: All before Skincare before other scopes, targets in TARGETS order."""
    scope_rank = {"All": 0, "Skincare": 1}
    target_rank = {t: i for i, t in enumerate(TARGETS)}
    keys = df[["scope", "target"]].drop_duplicates()
    keys = keys.assign(s=keys.scope.map(lambda s: scope_rank.get(s, 2)),
                       t=keys.target.map(target_rank)).sort_values(["s", "scope", "t"])
    return list(zip(keys.scope, keys.target))


# ------------------------------------------------------------------ figures

def fig_attrition(assoc):
    """Raw-significant vs adjusted-significant vs robust associations, per scope and target."""
    a = assoc[~((assoc.target == "rec_rate") & (assoc.scope == "All"))]  # identical to Skincare
    counts = (a.groupby(["scope", "target"])
              .agg(raw=("q_raw", lambda q: (q < 0.05).sum()), adjusted=("q_adj", lambda q: (q < 0.05).sum()),
                   robust=("robust", "sum"), tests=("feature", "size")).reset_index())
    targets = [t for t in TARGETS if t in set(counts.target)]
    scopes = ["All", "Skincare", "Makeup", "Hair", "Fragrance", "Bath & Body"]
    fig, axes = plt.subplots(1, len(targets), figsize=(TWO_COL, 2.3), sharey=True)
    h = 0.26
    for ax, t in zip(axes, targets):
        c = counts[counts.target == t].set_index("scope").reindex(scopes)
        y = np.arange(len(scopes))
        for i, (col, color, label) in enumerate(zip(["raw", "adjusted", "robust"], ORDINAL,
                                                     ["q<0.05 raw", "q<0.05 adjusted", "robust (both)"])):
            ax.barh(y + (i - 1) * h, c[col].fillna(0), height=h, color=color, edgecolor="white",
                    linewidth=0.6, label=label)
        ax.set_title(SHORT[t], color=INK)
        ax.set_yticks(y, scopes)
        ax.invert_yaxis()
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("associations")
    axes[0].legend(loc="upper center", bbox_to_anchor=(len(targets) / 2 + 0.1, 1.32), ncol=3, frameon=False)
    fig.subplots_adjust(wspace=0.12)
    save(fig, "fig_attrition")


def fig_model_comparison(folds):
    """Forest plot: Model B − Model A per model family, both validation schemes."""
    g = gains(folds)
    rows = ordered_rows(g)
    families = [("Linear (tuned)", lambda m: m in LINEAR), ("Random Forest", lambda m: m == "Random Forest"),
                ("LightGBM", lambda m: m == "LightGBM")]
    fig, axes = plt.subplots(1, 3, figsize=(TWO_COL, 3.0), sharey=True)
    y = np.arange(len(rows))
    for ax, (title, pick) in zip(axes, families):
        sub = g[g.model.map(pick)]
        for j, (cv, color, marker, label) in enumerate([("random", CAT[0], "o", "random 5-fold ×3"),
                                                        ("unseen_brand", CAT[1], "s", "unseen brands")]):
            s = sub[sub.cv == cv].set_index(["scope", "target"]).reindex(rows)
            yy = y + (j - 0.5) * 0.3
            ax.hlines(yy, s.lo, s.hi, color=color, linewidth=1.2)
            ax.plot(s.gain, yy, marker, color=color, markersize=4, markeredgecolor="white",
                    markeredgewidth=0.5, label=label, linestyle="none")
        ax.axvline(0, color=INK2, linewidth=0.8)
        ax.set_title(title, color=INK)
        ax.set_xlabel("Model B − Model A")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(y, [row_label(s, t) + (" (AUC)" if t == "high_performer" else " (R²)") for s, t in rows])
    axes[0].invert_yaxis()
    axes[1].legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=2, frameon=False)
    fig.subplots_adjust(wspace=0.1)
    save(fig, "fig_model_comparison")


def fig_shap_gap(shares, folds):
    """Share of SHAP attribution to ingredient features vs the actual gain from adding them."""
    g = gains(folds[(folds.model == "LightGBM") & (folds.cv == "random")])
    rows = ordered_rows(g)
    fams = [("baseline", "metadata"), ("ingredient", "ingredients"),
            ("functional_group", "functional groups"), ("combination", "combinations")]
    pivot = shares.pivot_table(index=["scope", "target"], columns="group", values="share").reindex(rows)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(TWO_COL, 2.6), sharey=True,
                                   gridspec_kw={"width_ratios": [1.6, 1]})
    y = np.arange(len(rows))
    left = np.zeros(len(rows))
    for (fam, label), color in zip(fams, ["#c3c2b7", CAT[0], CAT[2], CAT[3]]):
        v = pivot[fam].fillna(0).to_numpy()
        ax1.barh(y, v, left=left, height=0.62, color=color, edgecolor="white", linewidth=0.8, label=label)
        left += v
    ingredient_share = pivot[["ingredient", "functional_group", "combination"]].sum(axis=1).to_numpy()
    for yi, s in zip(y, ingredient_share):
        ax1.text(1.01, yi, f"{s:.0%}", va="center", fontsize=6.5, color=INK)
    ax1.text(1.01, -0.75, "non-\nmetadata", va="bottom", fontsize=6, color=INK2, linespacing=0.9)
    ax1.set_xlim(0, 1)
    ax1.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax1.set_xlabel("share of mean |SHAP| (Model B)")
    ax1.set_yticks(y, [row_label(s, t) for s, t in rows])
    ax1.invert_yaxis()
    ax1.grid(axis="y", visible=False)
    ax1.legend(loc="upper center", bbox_to_anchor=(0.5, 1.2), ncol=4, frameon=False,
               handlelength=1, columnspacing=0.8)

    s = g.set_index(["scope", "target"]).reindex(rows)
    ax2.hlines(y, s.lo, s.hi, color=CAT[0], linewidth=1.2)
    ax2.plot(s.gain, y, "o", color=CAT[0], markersize=4, markeredgecolor="white", markeredgewidth=0.5)
    ax2.axvline(0, color=INK2, linewidth=0.8)
    ax2.set_xlabel("gain from ingredients (ΔR² / ΔAUC)")
    ax2.grid(axis="y", visible=False)
    fig.subplots_adjust(wspace=0.18)
    save(fig, "fig_shap_gap")


def fig_associations(assoc, panels=(("All", "rating"), ("All", "log_loves"), ("Skincare", "rec_rate")), top=10):
    """Largest robust associations: adjusted effect with 95% CI, coloured by sign."""
    fig, axes = plt.subplots(1, len(panels), figsize=(TWO_COL, 2.9))
    for ax, (scope, target) in zip(axes, panels):
        a = assoc[(assoc.scope == scope) & (assoc.target == target) & assoc.robust]
        a = a.reindex(a.adj_beta.abs().sort_values(ascending=False).index).head(top).iloc[::-1]
        y = np.arange(len(a))
        colors = [POS if b > 0 else NEG for b in a.adj_beta]
        ax.hlines(y, a.adj_ci_low, a.adj_ci_high, color=colors, linewidth=1.2)
        ax.scatter(a.adj_beta, y, c=colors, s=16, edgecolors="white", linewidths=0.5, zorder=3)
        ax.axvline(0, color=INK2, linewidth=0.8)
        labels = [_shorten(pretty_feature(f)) for f in a.feature]
        ax.set_yticks(y, labels)
        ax.set_title(f"{scope} · {SHORT[target]}", color=INK)
        ax.set_xlabel("adjusted effect (SD)")
        ax.grid(axis="y", visible=False)
        if a.empty:
            ax.text(0.5, 0.5, "no robust associations", transform=ax.transAxes, ha="center", color=INK2)
    fig.subplots_adjust(wspace=1.25)
    save(fig, "fig_associations")


def _shorten(label, n=32):
    """Cut in the middle: combinations often share a prefix and differ only at the end."""
    if len(label) <= n:
        return label
    head = (n - 1) // 2
    return label[:head].rstrip() + "…" + label[-(n - 1 - head):].lstrip()


def fig_ablation(ablation_folds_cmp):
    """Model A vs ingredients-only vs Model B, per scope/target (LightGBM, random CV)."""
    c = ablation_folds_cmp
    rows = ordered_rows(c)
    fig, axes = plt.subplots(1, 2, figsize=(TWO_COL, 2.4), gridspec_kw={"width_ratios": [4, 1.4]})
    n_rows = max(sum(TARGETS[r[1]][0] == task for r in rows) for task in ("regression", "classification"))
    for ax, task, metric, label in [(axes[0], "regression", "r2", "R²"), (axes[1], "classification", "roc_auc", "ROC-AUC")]:
        rr = [r for r in rows if TARGETS[r[1]][0] == task]
        y = np.arange(len(rr))
        a = c[c.variant == "B"].set_index(["scope", "target"]).reindex(rr)
        only = c[c.variant == "ingredients_only"].set_index(["scope", "target"]).reindex(rr)
        # small vertical offsets so A and B stay visible when their scores almost coincide
        for vals, dy, color, marker, name in [(a[f"A_{metric}"], -0.17, CAT[0], "o", "A: metadata"),
                                              (only[f"B_{metric}"], 0.0, CAT[2], "D", "ingredients only"),
                                              (a[f"B_{metric}"], 0.17, CAT[1], "s", "B: metadata + ingredients")]:
            ax.plot(vals, y + dy, marker, color=color, markersize=4.5, markeredgecolor="white",
                    markeredgewidth=0.5, linestyle="none", label=name)
        ax.set_yticks(y, [row_label(s, t) for s, t in rr])
        ax.set_ylim(n_rows - 0.5, -0.5)  # same row spacing in both panels, rows from the top
        ax.set_xlabel(label)
        ax.grid(axis="y", visible=False)
    axes[0].legend(loc="upper center", bbox_to_anchor=(0.65, 1.18), ncol=3, frameon=False)
    fig.subplots_adjust(wspace=0.9)
    save(fig, "fig_ablation")


# ------------------------------------------------------------------ LaTeX

def tex(s):
    s = str(s)
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}"),
                 ("≥", r"$\geq$"), ("−", "--"), ("·", r"$\cdot$"), ("²", r"$^2$"), ("…", r"\ldots{}")]:
        s = s.replace(a, b)
    return s


def fmt_p(p):
    if p is None or (isinstance(p, float) and math.isnan(p)):
        return "--"
    return "$<$0.001" if p < 0.001 else f"{p:.3f}"


def fmt_signed(v, digits=3):
    """Math mode, so negatives get a real minus sign: $-0.407$."""
    return f"${v:+.{digits}f}$"


def write_table(name, header, rows, colspec, caption, label, note=None, wide=False, superheader=None):
    """Grid table in the department template style: ruled cells, shaded bold header row,
    italic caption *below*. `wide` is kept for call compatibility; the paper is single column.
    "MIDRULE" rows (group separators) become a double rule.
    `superheader`: optional [(text, span), ...] row above the header, e.g. to group columns by split."""
    cols = list(colspec) if isinstance(colspec, str) else colspec  # list allows p{..} / X columns
    grid = "|" + "|".join(cols) + "|"
    # a table with an X column wraps to exactly the text width (tabularx) instead of overflowing
    fit = any(c.endswith("X") for c in cols)  # "X" or ">{\raggedright...}X"
    begin = f"\\begin{{tabularx}}{{\\linewidth}}{{{grid}}}" if fit else f"\\begin{{tabular}}{{{grid}}}"
    lines = [r"\begin{table}[htbp]", r"\centering", r"\footnotesize" if fit else r"\small",
             *([r"\setlength{\tabcolsep}{3pt}"] if fit else []), begin, r"\hline"]
    if superheader:
        cells = []
        for i, (text, span) in enumerate(superheader):
            rule = "|c|" if i == 0 else "c|"
            body = f"\\textbf{{{text}}}" if text else ""
            cells.append(f"\\multicolumn{{{span}}}{{{rule}}}{{{body}}}")
        lines += [r"\rowcolor{headfill} " + " & ".join(cells) + r" \\", r"\hline"]
    lines += [r"\rowcolor{headfill} " + " & ".join(f"\\textbf{{{h}}}" for h in header) + r" \\", r"\hline"]
    for r in rows:
        if r == "MIDRULE":
            lines.append(r"\hline")
        elif isinstance(r, str) and r.startswith("GROUP:"):  # bold row spanning the table, e.g. "All, Rating"
            lines += [f"\\multicolumn{{{len(cols)}}}{{|l|}}{{\\cellcolor{{groupfill}}\\textbf{{{r[6:]}}}}} \\\\",
                      r"\hline"]
        else:
            lines += [" & ".join(str(c) for c in r) + r" \\", r"\hline"]
    lines.append(r"\end{tabularx}" if fit else r"\end{tabular}")
    if note:
        lines += [r"\par\smallskip", f"\\parbox{{0.95\\linewidth}}{{\\footnotesize {note}}}"]
    lines += [f"\\caption{{{caption}}}", f"\\label{{{label}}}", r"\end{table}"]
    TAB.mkdir(parents=True, exist_ok=True)
    (TAB / f"{name}.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  table   paper/tables/{name}.tex")


def tab_dataset(results):
    d = results["dataset"]
    t = d["targetsAvailable"]
    rows = [
        ["Catalogue products", f"{d['catalogue_products']:,}"],
        ["\\quad without an ingredient list", f"{d['no_ingredients']:,}"],
        ["\\quad multi-component kits", f"{d['multi_component_kits']:,}"],
        ["In scope (single formula; no sets, minis, tools)", f"{d['in_scope_before_dedup']:,}"],
        [r"\textbf{Analysed (one product per family)}", f"\\textbf{{{d['analysis_products']:,}}}"],
        "MIDRULE",
        ["Rating ($\\geq$25 reviews)", f"{t['rating']:,}"],
        ["Loves, review count, high-performer label", f"{t['log_loves']:,}"],
        ["Recommendation rate ($\\geq$25 votes; Skincare only)", f"{t['rec_rate']:,}"],
        "MIDRULE",
        ["Ingredient features in Model B", f"{d['ingredientFeatures']}"],
        ["\\quad of which mined combinations", f"{d['combinations']}"],
    ]
    write_table("tab_dataset", ["Stage / target", "Products"], rows, "lr",
                "Dataset construction and target coverage.", "tab:dataset")


def tab_models(comparison, full=False):
    c = comparison if full else comparison[comparison.model == "LightGBM"]
    rows, prev = [], None
    for r in c.itertuples():
        m = r.primary_metric
        a, b = getattr(r, f"A_{m}"), getattr(r, f"B_{m}")
        verdict = ("B" if r.gain > 0 else "A") if r.p_corrected < 0.05 else "--"
        if prev is not None and r.scope != prev:
            rows.append("MIDRULE")
        prev = r.scope
        rows.append([r.scope, SHORT[r.target], *( [r.model] if full else []),
                     "random" if r.cv == "random" else "unseen brand",
                     "AUC" if m == "roc_auc" else "$R^2$", f"{a:.3f}", f"{b:.3f}", fmt_signed(r.gain),
                     f"{r.b_wins}/{r.folds}", fmt_p(r.p_corrected), verdict])
    header = ["Scope", "Target", *(["Model"] if full else []), "Split", "Metric", "A", "B", r"$\Delta$",
              "B wins", "$p_{corr}$", "Better"]
    write_table("tab_models_full" if full else "tab_models", header, rows,
                "ll" + ("l" if full else "") + "llrrrrrc",
                ("Model A (metadata) vs Model B (+ingredient features), all models." if full else
                 "Model A (metadata) vs Model B (+ingredient features), LightGBM."),
                "tab:models_full" if full else "tab:models",
                note=r"$p_{corr}$: Nadeau--Bengio corrected resampled $t$-test over folds "
                     r"(15 for random, 5 for unseen brand). Better: variant significantly better at 0.05.",
                wide=True)


def tab_prespecified(assoc):
    p = assoc[assoc.prespecified & assoc.scope.isin(["All", "Skincare"])]
    rows = [[tex(pretty_feature(r.feature)), r.scope, SHORT[r.target], f"{r.n_with:,}", fmt_signed(r.effect),
             fmt_p(r.p_raw), fmt_signed(r.adj_beta), fmt_p(r.p_adj)] for r in p.itertuples()]
    write_table("tab_prespecified", ["Combination", "Scope", "Target", "$n$", "Raw", "$p$", r"Adj.\ $\beta$", "$p_{adj}$"],
                rows, "lllrrrrr", "Pre-specified combinations from the project proposal.", "tab:prespecified",
                note="Raw: Cliff's $\\delta$ (rate difference for high performer). Adj.\\ $\\beta$: brand-, "
                     "subcategory- and price-adjusted difference in outcome SD. Unadjusted for multiple testing "
                     "because the hypotheses were stated in advance.", wide=True)


def tab_robust(assoc, scope_targets=(("All", "rating"), ("All", "log_loves"), ("Skincare", "rec_rate")), top=6):
    rows = []
    for scope, target in scope_targets:
        a = assoc[(assoc.scope == scope) & (assoc.target == target) & assoc.robust]
        a = a.reindex(a.adj_beta.abs().sort_values(ascending=False).index).head(top)
        rows.append(f"GROUP:{scope}, {SHORT[target]}")  # once per group instead of a column on every row
        for r in a.itertuples():
            # full name, wrapped by the X column: this table is where the figure's shortened labels are spelled out
            rows.append([tex(pretty_feature(r.feature)), r.kind[:4] + ".",
                         f"{r.n_with:,}", fmt_signed(r.effect), fmt_signed(r.adj_beta),
                         f"[{fmt_signed(r.adj_ci_low, 2)}, {fmt_signed(r.adj_ci_high, 2)}]", fmt_p(r.q_adj)])
    write_table("tab_robust", ["Feature", "Kind", "$n$", r"Cliff's $\delta$",
                               r"Adj.\ $\beta$", r"95\% CI", "$q_{adj}$"], rows,
                [r">{\raggedright\arraybackslash}X", "l", "r", "r", "r", "c", "r"],
                "Largest robust associations (raw and adjusted $q<0.05$, same sign).", "tab:robust", wide=True)


def tab_ablation(abl):
    rows, prev = [], None
    for r in abl.itertuples():
        m = r.primary_metric
        if prev is not None and (r.scope, r.target) != prev:
            rows.append("MIDRULE")
        prev = (r.scope, r.target)
        rows.append([r.scope, SHORT[r.target], tex(r.variant), f"{getattr(r, f'B_{m}'):.3f}",
                     fmt_signed(r.gain), fmt_p(r.p_corrected), fmt_p(r.q_corrected)])
    write_table("tab_ablation", ["Scope", "Target", "Variant", "Score", r"$\Delta$ vs A", "$p_{corr}$", "$q$"], rows,
                "lllrrrr", "Ablation of ingredient feature families (LightGBM, random CV).", "tab:ablation",
                note="Score: $R^2$, or ROC-AUC for high performer. $q$: Benjamini--Hochberg over the three "
                     "single-family variants of all targets. B is the main comparison and ingredients\\_only "
                     "(no metadata) a reference point, so neither is tested here.", wide=True)


def tab_categories(cat):
    rows, prev = [], None
    for r in cat.itertuples():
        if prev is not None and r.scope != prev:
            rows.append("MIDRULE")
        prev = r.scope
        m = r.primary_metric
        rows.append([r.scope, SHORT[r.target], "random" if r.cv == "random" else "unseen brand",
                     f"{getattr(r, f'A_{m}'):.3f}", f"{getattr(r, f'B_{m}'):.3f}", fmt_signed(r.gain),
                     fmt_p(r.p_corrected), fmt_p(r.q_corrected)])
    write_table("tab_categories", ["Scope", "Target", "Split", "A", "B", r"$\Delta$", "$p_{corr}$", "$q$"], rows,
                "lllrrrrr", "Model A vs Model B within further categories (LightGBM).", "tab:categories",
                note="$q$: Benjamini--Hochberg over all rows of this table.", wide=True)


def tab_sensitivity(sens):
    s = sens[sens.model == "LightGBM"]
    rows = [[tex(r.setting), f"{r.products:,}", r.scope, SHORT[r.target], fmt_signed(r.gain), fmt_p(r.p_corrected),
             fmt_p(r.q_corrected)] for r in s.itertuples()]
    write_table("tab_sensitivity", ["Setting", "Products", "Scope", "Target", r"$\Delta$ (B--A)", "$p_{corr}$", "$q$"],
                rows, "lrllrrr", "Sensitivity of the Model A vs B comparison (LightGBM, 5-fold).",
                "tab:sensitivity", note="$q$: Benjamini--Hochberg within each setting.", wide=True)


# ------------------------------------------------------------------ compact tables (main_10page.tex)
# Same numbers as the tables above, pivoted so that each (scope, target) is one row.

def _groups(df):
    """(scope, target) groups in their order of appearance."""
    return list(dict.fromkeys(zip(df.scope, df.target)))


def _score(r, which):
    return getattr(r, f"{which}_{r.primary_metric}")


def _with_scope_rules(keys, make_row):
    rows, prev = [], None
    for scope, target in keys:
        if prev is not None and scope != prev:
            rows.append("MIDRULE")
        prev = scope
        rows.append(make_row(scope, target))
    return rows


def tab_models_compact(comparison):
    c = comparison[comparison.model == "LightGBM"]

    def row(scope, target):
        g = c[(c.scope == scope) & (c.target == target)].set_index("cv")
        out = [scope, SHORT[target], "AUC" if g.iloc[0].primary_metric == "roc_auc" else "$R^2$"]
        for cv in ["random", "unseen_brand"]:
            r = next(g.loc[[cv]].itertuples())
            out += [f"{_score(r, 'A'):.3f}", f"{_score(r, 'B'):.3f}", fmt_signed(r.gain), fmt_p(r.p_corrected)]
        return out

    n_sig = int((c.p_corrected < 0.05).sum())
    write_table("tab_models_compact", ["Scope", "Target", "Metric", "A", "B", r"$\Delta$", "$p_{corr}$",
                                       "A", "B", r"$\Delta$", "$p_{corr}$"],
                _with_scope_rules(_groups(c), row), "lllrrrrrrrr",
                "Model A (metadata) vs Model B (+ingredient features), LightGBM.", "tab:models",
                superheader=[("", 3), (r"Random 5-fold $\times$3", 4), ("Unseen brand", 4)],
                note=r"$p_{corr}$: Nadeau--Bengio corrected resampled $t$-test over folds (15 random, 5 unseen "
                     f"brand). Differences significant at 0.05: {n_sig} of {len(c)}.")


def tab_prespecified_compact(assoc):
    p = assoc[assoc.prespecified & assoc.scope.isin(["All", "Skincare"])]
    rows = []
    for feature in dict.fromkeys(p.feature):
        rows.append(f"GROUP:{tex(pretty_feature(feature))}")
        f = p[p.feature == feature]
        for target in dict.fromkeys(f.target):
            out = [SHORT[target]]
            for scope in ["All", "Skincare"]:
                r = next(f[(f.target == target) & (f.scope == scope)].itertuples())
                out += [f"{r.n_with:,}", fmt_signed(r.effect), fmt_p(r.p_raw), fmt_signed(r.adj_beta), fmt_p(r.p_adj)]
            rows.append(out)
    write_table("tab_prespecified_compact", ["Target", "$n$", "Raw", "$p$", r"Adj.\ $\beta$", "$p_{adj}$",
                                             "$n$", "Raw", "$p$", r"Adj.\ $\beta$", "$p_{adj}$"],
                rows, "lrrrrrrrrrr", "Pre-specified combinations from the project proposal.", "tab:prespecified",
                superheader=[("", 1), ("All products", 5), ("Skincare", 5)],
                note="Raw: Cliff's $\\delta$ (rate difference for high performer). Adj.\\ $\\beta$: brand-, "
                     "subcategory- and price-adjusted difference in outcome SD. Unadjusted for multiple testing "
                     "because the hypotheses were stated in advance. Recommendation rate exists for Skincare only.")


def tab_ablation_compact(abl):
    families = ["A+ingredients", "A+functional", "A+combinations"]

    def row(scope, target):
        g = abl[(abl.scope == scope) & (abl.target == target)].set_index("variant")
        first = next(g.itertuples())
        out = [scope, SHORT[target], f"{_score(first, 'A'):.3f}"]
        for v in families:
            r = next(g.loc[[v]].itertuples())
            out += [fmt_signed(r.gain), fmt_p(r.q_corrected)]
        return out + [f"{_score(next(g.loc[['ingredients_only']].itertuples()), 'B'):.3f}"]

    write_table("tab_ablation_compact", ["Scope", "Target", "A", r"$\Delta$", "$q$", r"$\Delta$", "$q$",
                                         r"$\Delta$", "$q$", "Score"],
                _with_scope_rules(_groups(abl), row), "llrrrrrrrr",
                "Ablation of ingredient feature families (LightGBM, random CV).", "tab:ablation",
                superheader=[("", 3), ("+ ingredients", 2), ("+ functional", 2), ("+ combinations", 2),
                             ("Ingr.\\ only", 1)],
                note="A: Model A score ($R^2$, or ROC-AUC for high performer). $\\Delta$: gain over A from adding "
                     "one feature family. $q$: Benjamini--Hochberg over all single-family variants. Ingr.\\ only: "
                     "a model with ingredient features and no metadata.")


def tab_categories_compact(cat):
    def row(scope, target):
        g = cat[(cat.scope == scope) & (cat.target == target)].set_index("cv")
        out = [scope, SHORT[target]]
        for cv in ["random", "unseen_brand"]:
            r = next(g.loc[[cv]].itertuples())
            out += [fmt_signed(r.gain), fmt_p(r.p_corrected), fmt_p(r.q_corrected)]
        return out

    write_table("tab_categories_compact", ["Scope", "Target", r"$\Delta$", "$p_{corr}$", "$q$",
                                           r"$\Delta$", "$p_{corr}$", "$q$"],
                _with_scope_rules(_groups(cat), row), "llrrrrrr",
                "Model B minus Model A within further categories (LightGBM).", "tab:categories",
                superheader=[("", 2), ("Random", 3), ("Unseen brand", 3)],
                note="$q$: Benjamini--Hochberg over all rows and both splits of this table.")


def tab_sensitivity_compact(sens):
    s = sens[sens.model == "LightGBM"]
    settings = list(dict.fromkeys(s.setting))

    def row(scope, target):
        out = [scope, SHORT[target]]
        for st in settings:
            r = next(s[(s.setting == st) & (s.scope == scope) & (s.target == target)].itertuples())
            out += [fmt_signed(r.gain), fmt_p(r.q_corrected)]
        return out

    products = {st: int(s[s.setting == st].products.iloc[0]) for st in settings}
    write_table("tab_sensitivity_compact", ["Scope", "Target"] + [r"$\Delta$", "$q$"] * len(settings),
                _with_scope_rules(_groups(s[s.setting == settings[0]]), row), "ll" + "rr" * len(settings),
                "Sensitivity of the Model A vs B comparison (LightGBM, 5-fold).", "tab:sensitivity",
                superheader=[("", 2)] + [(f"{tex(st).replace('>=', '$\\geq$')} ({products[st]:,})", 2)
                                         for st in settings],
                note="$\\Delta$: Model B minus Model A. $q$: Benjamini--Hochberg within each setting. "
                     "Product counts in parentheses.")


def numbers(results, assoc, comparison, shares):
    """Macros for numbers quoted in running text, so prose cannot drift from the data."""
    d = results["dataset"]
    non_metadata = shares[shares.group != "baseline"].groupby(["scope", "target"]).share.sum() * 100
    sig = comparison.p_corrected < 0.05
    a = assoc[~((assoc.target == "rec_rate") & (assoc.scope == "All"))]
    macros = {
        "NCatalogue": f"{d['catalogue_products']:,}",
        "NAnalysed": f"{d['analysis_products']:,}",
        "NInScope": f"{d['in_scope_before_dedup']:,}",
        "NRating": f"{d['targetsAvailable']['rating']:,}",
        "NRecRate": f"{d['targetsAvailable']['rec_rate']:,}",
        "NIngredientFeatures": str(d["ingredientFeatures"]),
        "NCombinations": str(d["combinations"]),
        "NComparisons": str(len(comparison)),
        "NBBetter": str(int((sig & (comparison.gain > 0)).sum())),
        "NABetter": str(int((sig & (comparison.gain < 0)).sum())),
        "NTests": f"{len(a):,}",
        "NSigRaw": f"{int((a.q_raw < 0.05).sum()):,}",
        "NSigAdj": f"{int((a.q_adj < 0.05).sum()):,}",
        "NRobust": f"{int(a.robust.sum()):,}",
        "MaxLGBMGain": f"{comparison[comparison.model == 'LightGBM'].gain.max():.3f}",
        "MinIngredientShare": f"{non_metadata.min():.0f}",
        "MaxIngredientShare": f"{non_metadata.max():.0f}",
    }
    if (DATA / "robustness_ablation.csv").exists():
        # ingredients-only vs Model A on all products (LightGBM, random CV), quoted in Results
        abl = pd.read_csv(DATA / "robustness_ablation.csv")
        only = abl[(abl.scope == "All") & (abl.variant == "ingredients_only")].set_index("target")
        for target, key in [("rating", "Rating"), ("log_loves", "Loves"), ("log_reviews", "Reviews")]:
            macros[f"Only{key}RTwo"] = f"{only.loc[target, 'B_r2']:.2f}"
            macros[f"A{key}RTwo"] = f"{only.loc[target, 'A_r2']:.2f}"
        macros["OnlyHPAUC"] = f"{only.loc['high_performer', 'B_roc_auc']:.2f}"
        macros["AHPAUC"] = f"{only.loc['high_performer', 'A_roc_auc']:.2f}"
    for name, file in [("Ablation", "robustness_ablation.csv"), ("Category", "robustness_categories.csv"),
                       ("Sensitivity", "robustness_sensitivity_models.csv")]:
        if (DATA / file).exists():
            r = pd.read_csv(DATA / file).dropna(subset=["q_corrected"])
            macros[f"N{name}Tests"] = str(len(r))
            macros[f"N{name}Nominal"] = str(int((r.p_corrected < 0.05).sum()))
            macros[f"N{name}FDR"] = str(int((r.q_corrected < 0.05).sum()))
            macros[f"Min{name}Q"] = f"{r.q_corrected.min():.2f}"
    lines = ["% generated by scripts/make_paper_assets.py - do not edit"]
    lines += [f"\\newcommand{{\\{k}}}{{{v}\\xspace}}" for k, v in macros.items()]
    TAB.mkdir(parents=True, exist_ok=True)
    (TAB / "numbers.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("  macros  paper/tables/numbers.tex")


def main():
    style()
    results = json.loads((DATA / "results.json").read_text(encoding="utf-8"))
    assoc = pd.read_csv(DATA / "associations.csv")
    folds = pd.read_csv(DATA / "cv_folds.csv")
    comparison = pd.read_csv(DATA / "model_comparison.csv")
    shares = pd.read_csv(DATA / "shap_group_shares.csv")

    fig_attrition(assoc)
    fig_model_comparison(folds)
    fig_shap_gap(shares, folds)
    fig_associations(assoc)
    tab_dataset(results)
    tab_models(comparison)
    tab_models(comparison, full=True)
    tab_prespecified(assoc)
    tab_robust(assoc)
    tab_models_compact(comparison)
    tab_prespecified_compact(assoc)
    numbers(results, assoc, comparison, shares)

    if (DATA / "robustness_ablation.csv").exists():
        abl = pd.read_csv(DATA / "robustness_ablation.csv")
        fig_ablation(abl)
        tab_ablation(abl)
        tab_ablation_compact(abl)
    else:
        print("  skipped ablation (run scripts/run_robustness.py)")
    if (DATA / "robustness_categories.csv").exists():
        cat = pd.read_csv(DATA / "robustness_categories.csv")
        tab_categories(cat)
        tab_categories_compact(cat)
    if (DATA / "robustness_sensitivity_models.csv").exists():
        sens = pd.read_csv(DATA / "robustness_sensitivity_models.csv")
        tab_sensitivity(sens)
        tab_sensitivity_compact(sens)
    else:
        print("  skipped sensitivity (run scripts/run_robustness.py)")


if __name__ == "__main__":
    main()
