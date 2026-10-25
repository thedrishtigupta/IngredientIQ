# Research Paper

The IEEE conference paper for the IngredientIQ research study. The method and findings are described in [docs/RESEARCH.md](../docs/RESEARCH.md).

## Build

**Overleaf (recommended, so all three of you can edit together).**
1. Zip the whole `paper/` folder, including `figures/` and `tables/`.
2. In Overleaf, choose New Project, then Upload Project.
3. Set the compiler to pdfLaTeX.

**Local.** Use any TeX distribution, then run `latexmk -pdf main.tex`.

## Never type a result by hand

Every number, table and figure is generated from the pipeline:

```powershell
python scripts/run_research.py           # main study, about 1 hour
python scripts/run_robustness.py         # ablation, per-category models, sensitivity, about 45 minutes
python scripts/make_paper_assets.py      # figures/*.pdf, tables/*.tex, tables/numbers.tex
```

- In prose, use the macros from `tables/numbers.tex`, e.g. `\NAnalysed{}` or `\NRobust{}`. Never type the digits.
- If you need a number that has no macro, add it to `numbers()` in [scripts/make_paper_assets.py](../scripts/make_paper_assets.py).
- If you change the pipeline, rerun all three scripts and re-upload `figures/` and `tables/`.

## Section status

| Section | Status | Suggested owner |
|---|---|---|
| Abstract | Outline: write last | Jhanvi |
| 1 Introduction | Outline | Drishti |
| 2 Related work | Outline: needs a literature search | All, one theme each |
| 3 Data | **Drafted** | Drishti: rewrite in your own words |
| 4 Method | **Drafted** | Arya: rewrite in your own words |
| 5 Results | **Drafted** (facts only) plus `\todo` items for interpretation | Arya + Jhanvi |
| 6 Discussion and limitations | Outline | Jhanvi |
| 7 Conclusion | Outline | Drishti |

The drafted sections are a starting point, not final text. Rewrite them in your own voice and make sure every one of you can explain every sentence in the viva.

## Before submitting

- [ ] Every `\todo{}` is resolved. Then change `\todo` to an empty macro in `main.tex` and check that no red text remains.
- [ ] The `sephoradata` entry in `references.bib` is filled in from the Kaggle page you actually used.
- [ ] Every bib entry is checked against its publisher page. Related-work papers have been read, not just found.
- [ ] The page limit and template match the venue's call for papers.
- [ ] AI-assistance disclosure is added if the venue requires one. Check its policy.
- [ ] Your guide has approved the author list and affiliations.
- [ ] The repository URL in the Reproducibility section is public.
