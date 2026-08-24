import json
from pathlib import Path

import pytest

from ingredients.parser import parse_ingredients, parse_outer_list, split_top_level


FIXTURES = json.loads(
    (Path(__file__).parent / "fixtures" / "ingredient_parser_fixtures.json").read_text(
        encoding="utf-8"
    )
)
BY_NAME = {x["test"]: x for x in FIXTURES}


def test_outer_list_parses_all_fixture_inputs():
    for fixture in FIXTURES:
        values = parse_outer_list(fixture["raw_ingredients"])
        assert values == fixture["raw_ingredients"]


def test_normal_ingredient_list_preserves_order_and_primary_context():
    f = BY_NAME["normal"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    assert len(records) > 5
    assert [r.position for r in records] == list(range(1, len(records) + 1))
    assert all(r.presence_type == "PRIMARY" for r in records)
    assert all(r.section == "main" for r in records)
    assert all(r.ingredient_name for r in records)


def test_commas_inside_parentheses_are_not_split():
    f = BY_NAME["parentheses_ci"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    names = [r.normalized_name for r in records]

    # The fixture contains Water (Aqua, Eau); it must remain one ingredient.
    assert "water (aqua, eau)" in names

    # CI codes are metadata, not independent ingredients.
    ci_records = [r for r in records if r.ci_codes]
    assert ci_records
    for r in ci_records:
        assert not r.normalized_name.startswith("ci ")
    # CI-only parenthetical metadata should not remain in the canonical name.
    raw_text = "Iron Oxides (CI 77491, CI 77492, CI 77499)"
    ci_test = parse_ingredients("TEST", [raw_text])[0]
    assert ci_test.normalized_name == "iron oxides"


def test_explicit_may_contain_is_separated():
    f = BY_NAME["may_contain"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    assert any(r.presence_type == "PRIMARY" for r in records)
    optional = [r for r in records if r.presence_type == "MAY_CONTAIN"]
    assert optional
    assert any(r.normalized_name == "titanium dioxide" for r in optional)
    assert all(r.section == "main" for r in records)


def test_semicolons_are_supported_without_breaking_parentheses():
    f = BY_NAME["semicolon"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    assert len(records) > 10
    assert all(r.ingredient_name for r in records)
    # Iron Oxides contains comma-separated CI codes inside parentheses.
    iron = [r for r in records if r.normalized_name.startswith("iron oxides")]
    assert iron
    assert len(iron[0].ci_codes) == 3


def test_outer_list_continuation_is_one_logical_stream():
    f = BY_NAME["continuation"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    assert len(records) >= 5
    assert [r.position for r in records] == list(range(1, len(records) + 1))
    assert all(r.section == "main" for r in records)


def test_component_labels_are_context_not_ingredients():
    f = BY_NAME["component"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    assert records
    assert not any(r.normalized_name in {"skin-enhancing tint", "light-catching highlighter", "lip treatment oil"} for r in records)
    sections = {r.section for r in records}
    assert {"skin-enhancing_tint", "light-catching_highlighter", "lip_treatment_oil"} <= sections


def test_step_context_is_preserved():
    f = BY_NAME["steps"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    sections = {r.section for r in records}
    assert "step_1" in sections
    assert "step_2" in sections
    assert any(r.normalized_name == "glycolic acid" and r.section == "step_1" for r in records)
    assert any(r.normalized_name == "retinol" and r.section == "step_2" for r in records)


def test_shade_context_is_preserved():
    f = BY_NAME["shades"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    sections = {r.section for r in records}
    assert "shade_1" in sections
    assert "shade_2" in sections
    assert any(r.section == "shade_1" for r in records)
    assert any(r.section == "shade_2" for r in records)


def test_percentage_is_extracted_and_preserved():
    f = BY_NAME["percentage"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    by_name = {r.normalized_name: r for r in records}
    assert by_name["octinoxate"].concentration == 7.5
    assert by_name["octinoxate"].concentration_unit == "%"
    assert by_name["titanium dioxide"].concentration == 2.0
    assert by_name["zinc oxide"].concentration == 17.1


def test_asterisk_is_metadata_not_identity():
    f = BY_NAME["asterisk"]
    records = parse_ingredients(f["product_id"], f["raw_ingredients"])
    tocopherol = next(r for r in records if r.normalized_name == "tocopherol (mixed)")
    squalane = next(r for r in records if r.normalized_name == "squalane")
    assert "*" in tocopherol.markers
    assert "*" in squalane.markers
    assert not tocopherol.normalized_name.startswith("*")


def test_split_top_level_respects_nested_delimiters():
    text = "Iron Oxides (CI 77491, CI 77492, CI 77499), Glycerin, Water (Aqua, Eau)"
    assert split_top_level(text) == [
        "Iron Oxides (CI 77491, CI 77492, CI 77499)",
        "Glycerin",
        "Water (Aqua, Eau)",
    ]


def test_empty_outer_elements_are_ignored():
    raw = "['Water, Glycerin', '', 'Niacinamide']"
    records = parse_ingredients("TEST", raw)
    assert [r.normalized_name for r in records] == ["water", "glycerin", "niacinamide"]


def test_parser_is_deterministic():
    for fixture in FIXTURES:
        a = [r.as_dict() for r in parse_ingredients(fixture["product_id"], fixture["raw_ingredients"])]
        b = [r.as_dict() for r in parse_ingredients(fixture["product_id"], fixture["raw_ingredients"])]
        assert a == b


def test_attached_and_spaced_markers_are_metadata():
    raw = ["Carmine* (CI 75470), * Sodium Benzoate, Potassium Sorbate (* - exfoliant)"]
    records = parse_ingredients("TEST", raw)
    carmine = next(r for r in records if r.normalized_name == "carmine")
    sodium = next(r for r in records if r.normalized_name == "sodium benzoate")
    sorbate = next(r for r in records if r.normalized_name.startswith("potassium sorbate"))
    assert "*" in carmine.markers
    assert "*" in sodium.markers
    assert "*" in sorbate.markers
    assert "*" not in carmine.normalized_name
    assert "*" not in sodium.normalized_name


def test_marked_footnote_suffix_does_not_become_ingredient_identity():
    raw = ["Limonene. *Antistatic agent/agent antistatique."]
    records = parse_ingredients("TEST", raw)
    assert len(records) == 1
    assert records[0].normalized_name == "limonene"
    assert "*" in records[0].markers
