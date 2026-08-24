# IngredientIQ — Ingredient Parser Test Contract v2

These are **real-data regression fixtures** selected from `product_info.csv`.

The tests are intentionally divided into:
- structural parsing
- semantic context
- metadata extraction
- preservation/invariants

The parser should be deterministic and should never silently discard source information.

---

## Proposed parsed record

The exact Python implementation can differ, but every ingredient record should expose equivalent information:

```python
{
    "product_id": "...",
    "ingredient_raw": "...",
    "ingredient_name": "...",
    "normalized_name": "...",
    "position": 1,
    "presence_type": "PRIMARY",
    "section": "main",
    "concentration": None,
    "concentration_unit": None,
    "ci_codes": [],
    "markers": []
}
```

`section` may use values such as `main`, `step_1`, `step_2`, `shade_1`, `contour`, etc.

---

# Test 1 — Normal single ingredient list

**Real fixture:** `normal`

### Must verify

- Outer list is parsed.
- Ingredients are split on top-level commas.
- Ingredient order is preserved.
- Every resulting ingredient has `presence_type = PRIMARY`.
- Default section is `main`.
- No punctuation-only records are produced.

### Core assertion

The first several ingredients in the parsed output must correspond exactly, in order, to the first several comma-delimited ingredients in the source.

---

# Test 2 — Parentheses / CI codes

**Real fixture:** `parentheses_ci`

### Must verify

For an ingredient such as:

```text
Iron Oxides (CI 77491, CI 77492, CI 77499)
```

the parser creates **one ingredient record**, not three.

Expected semantic result:

```text
ingredient_name = Iron Oxides
ci_codes = [
    CI 77491,
    CI 77492,
    CI 77499
]
```

### Critical assertion

No split occurs on commas inside parentheses.

---

# Test 3 — Explicit `May Contain`

**Real fixture:** `may_contain`

### Must verify

Ingredients before the `May Contain` boundary:

```text
PRIMARY
```

Ingredients after the boundary:

```text
MAY_CONTAIN
```

### Critical assertion

The same ingredient appearing in a primary section and a `May Contain` section must retain the appropriate context.

The `May Contain` marker itself must not become an ingredient.

---

# Test 4 — Semicolon-delimited format

**Real fixture:** `semicolon`

### Must verify

The parser recognizes semicolon-separated ingredients in the dataset.

Example semantic transformation:

```text
A; B; C
```

→

```text
A
B
C
```

while preserving nested constructs such as:

```text
Iron Oxides (CI 77491, CI 77492)
```

### Critical assertion

Delimiter handling must not destroy parentheses content.

---

# Test 5 — Multi-element continuation

**Real fixture:** `continuation`

### Must verify

When the outer list is:

```text
[
    "Ingredient A, Ingredient B, ...",
    "Ingredient C, Ingredient D, ..."
]
```

and neither element is a section label, the two elements are treated as a **single logical ingredient stream**.

### Critical assertions

- Ingredient order continues across the boundary.
- No fake ingredient is created from the list boundary.
- Position numbering remains continuous.

---

# Test 6 — Component/section product

**Real fixture:** `component`

### Must verify

Standalone labels such as:

```text
Contour:
Bronzer:
Highlighter:
```

are context, not ingredients.

Each following ingredient inherits the current section.

Example:

```text
Mica → contour
Mica → bronzer
```

### Critical assertion

Section labels never appear as ingredient records.

---

# Test 7 — Step-based formulation

**Real fixture:** `steps`

### Must verify

```text
Step 1:
...
Step 2:
...
```

creates separate contextual sections.

Expected:

```text
ingredients from Step 1 → section = step_1
ingredients from Step 2 → section = step_2
```

### Critical assertion

The parser must not flatten the two steps into an indistinguishable list.

---

# Test 8 — Shade-specific formulation

**Real fixture:** `shades`

### Must verify

```text
Shade 1:
...
Shade 2:
...
```

creates shade context.

Expected:

```text
ingredient → shade_1
ingredient → shade_2
```

### Critical assertion

An ingredient appearing only in Shade 1 must not automatically be represented as a universal product ingredient.

This distinction will matter later when product-level ingredient matching is implemented.

---

# Test 9 — Concentration / percentage

**Real fixture:** `percentage`

### Must verify

For:

```text
10% Glycolic Acid
0.5% Retinol
17.1% Zinc Oxide
```

extract:

```text
ingredient_name
concentration
concentration_unit
```

Example:

```text
10% Glycolic Acid

ingredient_name = Glycolic Acid
concentration = 10
concentration_unit = "%"
```

### Critical assertion

The concentration must survive normalization.

---

# Test 10 — Asterisk markers

**Real fixture:** `asterisk`

### Must verify

For:

```text
*Tocopherol
```

produce:

```text
ingredient_name = Tocopherol
markers = ["*"]
```

For:

```text
Salicylic Acid*
```

produce:

```text
ingredient_name = Salicylic Acid
markers = ["*"]
```

### Critical assertion

The asterisk must not become part of the canonical ingredient name.

The raw representation must remain available.

---

# Cross-cutting invariant A — Raw traceability

Every output record must retain:

```text
product_id
ingredient_raw
```

This allows us to trace every normalized ingredient back to the source dataset.

---

# Cross-cutting invariant B — Stable ordering

For primary ingredients:

```text
position = 1, 2, 3, ...
```

must follow the source order.

Contextual sections may reset or continue position, but the choice must be explicit and consistent.

---

# Cross-cutting invariant C — No empty ingredients

Empty fragments must not become ingredient records.

The parser must handle the one observed empty list element without crashing.

---

# Cross-cutting invariant D — Determinism

For identical input:

```python
parse(raw) == parse(raw)
```

The parser should always return the same semantic output.

---

# Cross-cutting invariant E — No accidental ingredient creation

The following must never independently become ingredients merely because they occur in the source:

```text
CI 77491
Step 1:
Shade 2:
May Contain:
*
(+/-)
```

They are metadata/context unless the source explicitly represents something else.

---

# Cross-cutting invariant F — Parentheses safety

This is a mandatory regression test.

For every product containing commas inside parentheses:

```python
parenthesis_depth > 0
```

must prevent comma splitting.

The parser should be validated across **all 7,549 ingredient-bearing products**, not just the ten fixtures.

---

# Acceptance Criteria

The parser is ready for the next stage only when:

- All ten real-data fixtures pass.
- No comma inside parentheses causes a false split.
- `May Contain` is represented separately from primary ingredients.
- Multi-section products preserve context.
- Step context is preserved.
- Shade context is preserved.
- Concentrations are preserved.
- CI codes are preserved as metadata.
- Asterisk markers are preserved as metadata.
- Ingredient ordering is deterministic.
- Raw ingredient text remains traceable.
- Empty fragments do not crash parsing.
- All 7,549 products can be processed without unhandled exceptions.
- Parser output passes basic sanity checks (no empty names, no obvious labels as ingredients, no malformed positions).

---

# Important implementation rule

Do **not** overfit the parser to these ten fixtures.

These are regression tests representing known edge cases.

After implementation, run the parser over the complete ingredient-bearing dataset and generate a failure/quality report.

The intended loop is:

```text
Real examples
    ↓
Tests
    ↓
Parser
    ↓
Run on 7,549 products
    ↓
Find new edge cases
    ↓
Add regression test
    ↓
Fix parser
    ↓
Repeat
```

This is how we make the parser robust rather than merely making ten examples pass.
