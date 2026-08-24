from ingredients.parser import parse_ingredients


def test_inline_step_prefix_is_context_not_ingredient():
    records = parse_ingredients("P", ["Step 1: Water/Aqua/Eau, Glycolic Acid, Glycerin"])
    assert [r.normalized_name for r in records] == ["water/aqua/eau", "glycolic acid", "glycerin"]
    assert all(r.section == "step_1" for r in records)


def test_inline_shade_prefix_is_context_not_ingredient():
    records = parse_ingredients("P", [
        "Shade: Pillow Talk",
        "Mica, Squalane",
        "Shade: Sunset",
        "Mica, Dimethicone",
    ])
    assert all("shade:" not in r.normalized_name for r in records)
    assert {r.section for r in records} == {"shade_pillow_talk", "shade_sunset"}


def test_may_contain_variants_are_optional():
    records = parse_ingredients("P", [
        "Mica, Talc. May Contain/Peut Contenir: Titanium Dioxide (CI 77891), Iron Oxides (CI 77491, CI 77492)",
        "Water, Glycerin. May Contain (+/-): Yellow 5 Lake (CI 19140)",
        "Water, Glycerin. [+/- Titanium Dioxide (CI 77891), Iron Oxides (CI 77499)]",
    ])
    assert all(r.presence_type == "PRIMARY" for r in records[:2])
    assert any(r.normalized_name == "titanium dioxide" and r.presence_type == "MAY_CONTAIN" for r in records)
    assert any(r.normalized_name == "iron oxides" and r.presence_type == "MAY_CONTAIN" for r in records)
    assert not any(r.normalized_name.startswith("may contain") for r in records)


def test_standalone_component_labels_are_sections():
    records = parse_ingredients("P", ["Tempera:", "Mica, Talc", "Glistening:", "Mica, Squalane"])
    assert {r.section for r in records} == {"tempera", "glistening"}
    assert not any(r.normalized_name in {"tempera", "glistening"} for r in records)


def test_ci_parenthetical_is_one_record():
    records = parse_ingredients("P", ["Iron Oxides (CI 77491, CI 77492, CI 77499), Water (Aqua, Eau)"])
    assert len(records) == 2
    iron = records[0]
    assert iron.normalized_name == "iron oxides"
    assert iron.ci_codes == ("CI 77491", "CI 77492", "CI 77499")


def test_descriptive_colon_text_is_not_treated_as_section_when_inline():
    records = parse_ingredients("P", ["Avocado: Contains vitamins and minerals."])
    assert records[0].normalized_name == "avocado: contains vitamins and minerals"


def test_optional_marker_is_not_an_ingredient():
    records = parse_ingredients("P", [
        "Water, Glycerin. May Contain: (+/-), Iron Oxide (CI 77499)"
    ])
    assert not any(r.normalized_name in {"+/-", "may contain"} for r in records)
    assert any(r.normalized_name == "iron oxide" and r.presence_type == "MAY_CONTAIN" for r in records)


def test_nano_brackets_are_preserved():
    records = parse_ingredients("P", ["Black 2 (CI 77266) [Nano]"])
    assert records[0].ingredient_name == "Black 2 (CI 77266) [Nano]"
    assert records[0].normalized_name == "black 2 (ci 77266) [nano]"


def test_plus_minus_bilingual_boundary_is_optional():
    records = parse_ingredients("P", [
        "Mica, Sorbic Acid +/- May Contain/Peut Contenir: Titanium Dioxide (CI 77891), Iron Oxides (CI 77491)"
    ])
    assert [r.normalized_name for r in records[:2]] == ["mica", "sorbic acid"]
    assert all(r.presence_type == "MAY_CONTAIN" for r in records[2:])
    assert not any("may contain" in r.normalized_name for r in records)
