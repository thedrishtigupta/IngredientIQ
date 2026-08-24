# IngredientIQ — Ingredient Data Profiling

## Purpose

This document records the findings from profiling the actual `ingredients` column in the supplied `product_info.csv`.

**Scope:** This phase is focused only on building the IngredientIQ product recommendation system. The separate research/ingredient-success prediction track is intentionally out of scope for now.

---

# 1. Dataset Overview

The supplied product dataset contains:

- **8,494 products**
- **7,549 products with non-empty ingredient data**
- **945 products without ingredient data**
- Ingredient coverage: **88.87%**

The `ingredients` column is stored as a Python-style list string.

Example:

```text
['Water, Glycerin, Niacinamide, ...']
```

All 7,549 non-empty ingredient values were successfully parsed as Python-style lists using `ast.literal_eval()`.

---

# 2. Outer Structure of the Ingredient Data

The outer list structure is highly consistent.

| Structure | Count |
|---|---:|
| Single-element lists | 6,540 |
| Multi-element lists | 1,009 |
| Maximum list elements in one product | 115 |
| Median list elements | 1 |
| Mean list elements | 1.81 |

Therefore, the first stage of parsing can safely be:

```python
ast.literal_eval(raw_ingredients)
```

However, the resulting list elements still contain semi-structured ingredient text that requires additional parsing.

---

# 3. Major Finding: Do NOT Split Ingredients Naively by Comma

A simple operation such as:

```python
ingredient_string.split(",")
```

is unsafe.

### Why?

**1,152 products (15.26%)** contain commas inside parentheses.

Examples include:

```text
Iron Oxides (CI 77491, CI 77492, CI 77499)
```

and chemical names such as:

```text
(3r,3as,6s,7r)-6-Methoxy...
```

A naive comma split would incorrectly break these into multiple ingredients.

Therefore, ingredient splitting must track **parenthesis depth** and only split on commas occurring at depth `0`.

---

# 4. Ingredient Format Categories Observed

The profiling identified several major structural cases.

## 4.1 Normal single ingredient list

Example:

```text
['Water, Glycerin, Niacinamide, ...']
```

This is the most common case.

---

## 4.2 `May Contain` / Optional Pigments

Examples:

```text
... Phenoxyethanol.
May Contain: Titanium Dioxide, Iron Oxides, ...
```

or:

```text
... [+/- Titanium Dioxide (...); Iron Oxides (...)]
```

Observed markers:

- `May Contain`
- `+/-`
- `[+/- ...]`

The system should distinguish these ingredients from the main formulation rather than treating them identically.

A useful representation is:

```text
presence_type = PRIMARY
```

versus:

```text
presence_type = MAY_CONTAIN
```

This distinction will be especially useful for makeup products.

---

# 5. Multi-Element Ingredient Lists

There are **1,009 products** whose outer ingredient list contains multiple elements.

These do not all have the same meaning.

## 5.1 Continuation fragments

Example:

```text
[
    "Water, Denatured Alcohol, Fragrance, ...",
    "Butyl Methoxydibenzoylmethane, ..."
]
```

These are effectively one continuous ingredient list that has been split across multiple outer list elements.

These should generally be joined before ingredient-level splitting.

---

## 5.2 Component/Section-based products

Example:

```text
[
    "Contour:",
    "Mica, Talc, Iron Oxides, ...",
    "Bronzer:",
    "Mica, Talc, ..."
]
```

Here the section information is meaningful.

A future structured representation should retain:

```text
section = contour
section = bronzer
```

rather than flattening everything without context.

---

## 5.3 Multi-step formulations

A small number of products use:

```text
Step 1:
...
Step 2:
...
```

There were approximately **10 products** using this structure.

The parser should explicitly support step information.

---

## 5.4 Shade-specific formulations

Some palettes contain structures such as:

```text
Shade 1:
...
Shade 2:
...
Shade 3:
...
```

The shade context should be retained where possible.

---

# 6. Important Markers

The profiling found the following markers:

| Marker | Products |
|---|---:|
| `CI` color codes | 3,172 |
| `+/-` | 970 |
| `%` concentration | 376 |
| `*` markers | 407 |
| `**` markers | 88 |
| Semicolons | 33 |
| Colons | 1,482 |
| Angle-bracket markers | 241 |

These markers should not simply be discarded during cleaning because some contain useful structural or metadata information.

---

# 7. CI Color Codes

CI codes are extremely common: approximately **42.02%** of products contain them.

Example:

```text
Iron Oxides (CI 77491, CI 77492, CI 77499)
```

The parser should not automatically create three independent ingredients:

```text
CI 77491
CI 77492
CI 77499
```

Instead, the meaningful ingredient entity can remain:

```text
Iron Oxides
```

while the CI codes are retained as metadata:

```json
{
  "ingredient_name": "Iron Oxides",
  "ci_codes": [
    "CI 77491",
    "CI 77492",
    "CI 77499"
  ]
}
```

---

# 8. Percentage-Labelled Ingredients

There are **376 products** containing percentage-labelled ingredients.

Examples:

```text
10% Glycolic Acid
0.5% Retinol
17.1% Zinc Oxide
```

The parser should preserve the concentration rather than simply stripping it.

Potential representation:

```json
{
  "ingredient_name": "Glycolic Acid",
  "concentration": 10,
  "concentration_unit": "%"
}
```

---

# 9. Asterisk Markers

There are **407 products** containing `*` markers.

Examples:

```text
*Tocopherol
*Beta-Sitosterol
*Squalane
```

and:

```text
Salicylic Acid*
```

The `*` should not become part of the canonical ingredient name.

However, the marker itself should initially be preserved as metadata:

```json
{
  "ingredient_raw": "*Tocopherol",
  "ingredient_name": "Tocopherol",
  "markers": ["*"]
}
```

We should not assume the exact semantic meaning of every marker until we inspect the surrounding product information.

---

# 10. Semicolon-Based Formatting

Only **33 products** contain semicolon-heavy ingredient formatting.

Example:

```text
Polybutene;
Hydrogenated Polyisobutene;
Dextrin Palmitate;
...
```

Some of these also contain:

```text
May Contain:
```

and pigment lists.

The parser therefore needs to support semicolon delimiters in addition to commas.

However, semicolon handling should also be implemented carefully rather than blindly replacing every semicolon.

---

# 11. Parentheses Are Structurally Important

The ingredient parser must understand parentheses.

For example:

```text
Water/Aqua/Eau
Iron Oxides (CI 77491, CI 77492, CI 77499)
```

The commas inside the parentheses belong to the same ingredient.

Therefore, the intended splitting logic is conceptually:

```text
split on comma
ONLY IF parenthesis_depth == 0
```

The profiling found:

- **1,152 products** with commas inside parentheses
- **4,264 commas** occurring inside parentheses
- Maximum observed parenthesis depth: **46**

The maximum depth is unusually high and means the parser should track depth rather than relying on simplistic regex assumptions.

---

# 12. Standalone Section Labels

Across the parsed list elements, **93 elements** looked like standalone section labels, appearing in **33 products**.

Examples:

```text
Step 1:
Step 2:

Highlighter:
Bronzer:
Blush:
Contour:

Shade 1:
Shade 2:
Shade 3:
...
```

These should be treated as metadata/context rather than ingredients.

---

# 13. Proposed Ingredient Representation

For the cleaned ingredient layer, a record could look like:

```json
{
  "product_id": "P123",
  "ingredient_raw": "Iron Oxides (CI 77491, CI 77492, CI 77499)",
  "ingredient_name": "Iron Oxides",
  "normalized_name": "iron oxides",
  "position": 12,
  "presence_type": "PRIMARY",
  "section": "main",
  "concentration": null,
  "concentration_unit": null,
  "ci_codes": [
    "CI 77491",
    "CI 77492",
    "CI 77499"
  ],
  "markers": []
}
```

For an ingredient with concentration:

```json
{
  "ingredient_name": "Glycolic Acid",
  "normalized_name": "glycolic acid",
  "concentration": 10,
  "concentration_unit": "%"
}
```

---

# 14. Two Levels of Ingredient Representation

The system should maintain both:

## Level 1 — Product-level ingredient representation

This answers:

> What ingredients are associated with this product?

Example:

```text
Product A
 ├── glycerin
 ├── niacinamide
 ├── dimethicone
 └── fragrance
```

This is the primary representation needed by the recommendation engine.

## Level 2 — Contextual ingredient representation

This retains information such as:

```text
product_id
ingredient
position
presence_type
section
concentration
CI codes
markers
```

Example:

```text
P123 | mica       | 15 | MAY_CONTAIN | shade_1
P123 | glycerin   | 5  | PRIMARY     | main
P123 | niacinamide| 7  | PRIMARY     | main
```

This gives the system more information without making the initial recommendation engine unnecessarily complicated.

---

# 15. Proposed Ingredient Processing Pipeline

The parser should be built as a pipeline rather than one large function.

```text
Raw ingredient string
        ↓
1. Parse outer Python-style list
        ↓
2. Detect sections/components
        ↓
3. Join continuation fragments
        ↓
4. Separate PRIMARY / MAY_CONTAIN
        ↓
5. Split ingredient text safely
   (comma outside parentheses)
        +
   semicolon handling
        ↓
6. Clean individual ingredient
        ↓
7. Extract metadata
   ├── percentage
   ├── CI codes
   └── markers
        ↓
8. Normalize ingredient name
        ↓
Structured ingredient records
```
