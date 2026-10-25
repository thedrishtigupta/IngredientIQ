"""Run the ingredient-success research study (synopsis section 2.6) end to end.

Reads the CSVs in data/raw and data/processed (no database needed) and writes:
    data/research/*.csv / products.parquet   every table, for the paper
    data/research/results.json               summary used by the web page
    client/src/lib/research-results.json     copy the /research page imports
    docs/RESEARCH_RESULTS.md                  generated tables

Run:  python scripts/run_research.py                 (full run, ~1 hour: mostly step 5)
      python scripts/run_research.py --quick         (1 CV repeat, LightGBM only: a few minutes)
      python scripts/run_research.py --reuse-models  (redo everything except step 5's CV)
"""

import argparse
import json
from pathlib import Path
import sys
import time
import warnings

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research import explain, models, report  # noqa: E402
from research.combos import add_combo_features, mine_combinations, untestable_prespecified  # noqa: E402
from research.dataset import build_study_data, load_sources  # noqa: E402
from research.stats import association_tests, functional_group_tests, summarize  # noqa: E402

OUT = ROOT / "data" / "research"
CLIENT_JSON = ROOT / "client" / "src" / "lib" / "research-results.json"
REPORT = ROOT / "docs" / "RESEARCH_RESULTS.md"


def step(title):
    print(f"\n== {title}", flush=True)
    return time.time()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--quick", action="store_true", help="1 CV repeat and LightGBM only")
    parser.add_argument("--reuse-models", action="store_true", help="load step-5 fold scores from the last run")
    args = parser.parse_args()
    warnings.filterwarnings("ignore", category=UserWarning)
    warnings.filterwarnings("ignore", category=FutureWarning)
    OUT.mkdir(parents=True, exist_ok=True)

    t = step("Steps 1-2: analysis dataset and targets")
    study = build_study_data(load_sources(ROOT / "data"))
    print(json.dumps(study.notes, indent=2))

    t = step("Step 4: frequent ingredient combinations (FP-Growth)")
    combos = mine_combinations(study.frame, study.ingredient_cols)
    study.frame, study.combo_cols = add_combo_features(study.frame, combos)
    combos.assign(items=combos["items"].map(" + ".join)).to_csv(OUT / "combinations.csv", index=False)
    study.frame.to_parquet(OUT / "products.parquet", index=False)
    print(f"{len(combos)} combinations; {combos.category.value_counts().to_dict()}  ({time.time() - t:.0f}s)")

    t = step("Step 3: association tests (raw + brand/subcategory-adjusted, BH-corrected)")
    assoc = association_tests(study, combos)
    fg = functional_group_tests(study)
    assoc.to_csv(OUT / "associations.csv", index=False)
    fg.to_csv(OUT / "functional_groups.csv", index=False)
    print(summarize(assoc).to_string(index=False))
    print(f"({time.time() - t:.0f}s)")

    t = step("Step 5: Model A vs Model B cross-validation")
    folds_path = OUT / "cv_folds.csv"
    if args.reuse_models:
        import pandas as pd
        folds = pd.read_csv(folds_path)
        print(f"reused {len(folds)} fold scores from {folds_path.name}")
    else:
        if args.quick:
            models.REPEATS = 1
        folds = models.cross_validate(study, model_names=["LightGBM"] if args.quick else None)
        folds.to_csv(folds_path, index=False)
    comparison = models.compare(folds)
    comparison.to_csv(OUT / "model_comparison.csv", index=False)
    cols = ["scope", "target", "cv", "model", "primary_metric", "gain", "b_wins", "folds", "p_corrected"]
    print(comparison[cols].to_string(index=False))
    print(f"({time.time() - t:.0f}s)")

    t = step("Step 6: SHAP explainability + cross-check with step 3")
    importance, shares = explain.explain(study, assoc)
    importance.to_csv(OUT / "shap_importance.csv", index=False)
    shares.to_csv(OUT / "shap_group_shares.csv", index=False)
    print(shares.pivot_table(index=["scope", "target"], columns="group", values="share").round(3).to_string())
    print(f"({time.time() - t:.0f}s)")

    step("Export")
    results = report.build_results(study, untestable_prespecified(study.frame), assoc, fg,
                                   comparison, importance, shares)
    text = json.dumps(results, indent=2, ensure_ascii=False)
    (OUT / "results.json").write_text(text, encoding="utf-8")
    CLIENT_JSON.write_text(text, encoding="utf-8")
    report.write_markdown(REPORT, results, assoc, fg, comparison, importance, shares)
    print(f"wrote {OUT.relative_to(ROOT)}/, {CLIENT_JSON.relative_to(ROOT)}, {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
