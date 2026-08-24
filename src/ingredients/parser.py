from __future__ import annotations

import ast
import re
from typing import Iterable

from .models import IngredientRecord
from .normalizer import normalize_ingredient_name, normalize_whitespace


_LABEL_PATTERNS = [
    (re.compile(r"^step\s*(\d+)\s*:?$", re.I), "step_{}"),
    (re.compile(r"^shade\s*(\d+)\s*:?$", re.I), "shade_{}"),
    (re.compile(r"^(shade|shades|color|colour)\s*:?$", re.I), None),
    (re.compile(
        r"^(highlighter|blush|bronzer|contour|eyeshadows?|lip(?:stick|gloss|color)?|foundation|primer|powder|shampoo|conditioner|liner|scalp treatment|body lotion|cream blush)\s*:?$",
        re.I,
    ), "{}"),
]

# A section label can occur either as a standalone outer-list element or as a
# prefix to the ingredient stream, e.g. ``Step 1: Water, Glycerin`` or
# ``Shade: Pillow Talk``.  We intentionally keep this conservative: ordinary
# explanatory text such as ``Avocado: Contains ...`` is not treated as a
# formulation section unless it is a standalone outer-list element.
_INLINE_SECTION_RE = re.compile(
    r"^\s*(step\s*\d+|shade\s*\d+|shade|shades|color|colour)\s*:\s*(.*?)\s*$",
    re.I,
)

_PRESENCE_PATTERNS = [
    # May Contain / Peut Contenir, optionally wrapped and optionally followed
    # by (+/-), e.g. ``[May Contain]: Mica`` or ``May Contain (+/-): Mica``.
    re.compile(
        r"(?:\[\s*)?(?:may\s+contain|peut\s+contenir)"
        r"(?:\s*/\s*(?:may\s+contain|peut\s+contenir))*"
        r"\s*:?\s*(?:(?:\(\s*)?(?:\+/-|±)(?:\s*\))?)?\s*"
        r"(?:\]\s*)?",
        re.I,
    ),
    # Optional pigment marker before the bilingual phrase, e.g.
    # ``[+/- (May Contain/Peut Contenir): ...]``.
    re.compile(
        r"(?:(?:\[|\()\s*)?(?:\+/-|±)\s*"
        r"(?:\s*\)\s*)?(?:(?:\[\s*|\(\s*)?(?:may\s+contain|peut\s+contenir)"
        r"(?:\s*/\s*(?:may\s+contain|peut\s+contenir))*"
        r"\s*:?\s*(?:\]|\))?\s*)?"
        r"(?:\]\s*)?",
        re.I,
    ),
    # Bare ``+/-`` forms such as ``[+/-: Mica]``.
    re.compile(
        r"(?:\[\s*)?(?:\+/-|±)\s*:?\s*",
        re.I,
    ),
]

_PERCENT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*")
_PERCENT_SUFFIX_RE = re.compile(r"\s+(\d+(?:\.\d+)?)\s*%\s*$")
_CI_RE = re.compile(r"\bCI\s*\d{4,6}\b", re.I)


def parse_outer_list(raw: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(raw, (list, tuple)):
        return [str(x) for x in raw]
    if not isinstance(raw, str):
        raise TypeError(f"ingredients must be str/list/tuple, got {type(raw)!r}")

    value = raw.strip()
    if not value:
        return []

    parsed = ast.literal_eval(value)
    if not isinstance(parsed, list):
        raise ValueError("Ingredient value is not a list")
    return [str(x) for x in parsed]


def _slug(value: str) -> str:
    value = normalize_whitespace(value).strip(" :;,.[]()")
    value = re.sub(r"[^\w\s&+.-]", "", value, flags=re.UNICODE)
    value = re.sub(r"[\s/]+", "_", value)
    return value.casefold().strip("_") or "main"


def _section_label(value: str) -> str | None:
    """Recognize a standalone outer-list section label."""
    original = normalize_whitespace(value)
    stripped = original.strip(" :")

    for pattern, formatter in _LABEL_PATTERNS:
        match = pattern.fullmatch(stripped)
        if match:
            if formatter is None:
                # ``Shade:`` / ``Shades:`` without a value are generic labels.
                return _slug(match.group(1))
            if formatter == "{}":
                return _slug(match.group(1))
            return formatter.format(match.group(1))

    # Real dataset contains many component/shade names as standalone labels,
    # e.g. ``Tempera:``, ``Glistening:``, ``Powder:`` and long product-component
    # names. Treat a short, colon-terminated outer element as a section only.
    if (
        original.endswith(":")
        and 1 < len(original) <= 100
        and not any(ch in original for ch in ",;[]")
        and not re.search(r"%\s*$", original)
    ):
        return _slug(stripped)

    return None


def _split_inline_section(value: str) -> tuple[str | None, str]:
    """Extract only explicit formulation prefixes such as ``Step 1:``.

    ``Shade: Lip Cheat In Pillow Talk Medium`` is represented as a section
    header with no ingredient payload. ``Step 1: Water, ...`` has both a
    section and an ingredient payload.
    """
    match = _INLINE_SECTION_RE.match(value)
    if not match:
        return None, value

    label = match.group(1).strip()
    remainder = match.group(2).strip()
    label_l = label.casefold()

    if label_l.startswith("step"):
        number = re.search(r"\d+", label_l)
        section = f"step_{number.group(0)}" if number else _slug(label)
        return section, remainder

    if label_l.startswith("shade"):
        # If a shade value is supplied, preserve it as context. This is useful
        # for sets where the source uses ``Shade: Pillow Talk`` rather than
        # ``Shade 1:``.
        if remainder and not _looks_like_ingredient_stream(remainder):
            return f"shade_{_slug(remainder)}", ""
        return _slug(label), remainder

    return _slug(label), remainder


def _looks_like_ingredient_stream(value: str) -> bool:
    """Heuristic used only for inline Shade/Step context decisions."""
    # A comma/semicolon is a strong signal of an ingredient stream. A single
    # well-known ingredient also counts; otherwise a short shade name should
    # remain metadata rather than becoming an ingredient.
    if "," in value or ";" in value or "%" in value:
        return True
    if re.search(r"\b(?:water|aqua|glycerin|dimethicone|mica|talc|alcohol|parfum)\b", value, re.I):
        return True
    return False


def split_top_level(text: str, delimiters: str = ",;") -> list[str]:
    """Split only when outside (), [] and {}."""
    result: list[str] = []
    current: list[str] = []
    stack: list[str] = []
    matching = {")": "(", "]": "[", "}": "{",
    }

    for char in text:
        if char in "([{":
            stack.append(char)
            current.append(char)
            continue
        if char in ")]}":
            if stack and stack[-1] == matching[char]:
                stack.pop()
            current.append(char)
            continue
        if char in delimiters and not stack:
            item = normalize_whitespace("".join(current))
            if item:
                result.append(item)
            current = []
        else:
            current.append(char)

    item = normalize_whitespace("".join(current))
    if item:
        result.append(item)
    return result


def _nesting_depth_at(text: str, index: int) -> int:
    stack: list[str] = []
    matching = {")": "(", "]": "[", "}": "{"}
    for char in text[:index]:
        if char in "([{":
            stack.append(char)
        elif char in ")] }".replace(" ", ""):
            if stack and stack[-1] == matching[char]:
                stack.pop()
    return len(stack)


def _find_presence_boundary(text: str) -> tuple[int, int] | None:
    """Find the first optional-ingredient marker beginning at top level."""
    candidates: list[tuple[int, int]] = []
    for pattern in _PRESENCE_PATTERNS:
        for match in pattern.finditer(text):
            if _nesting_depth_at(text, match.start()) == 0:
                candidates.append((match.start(), match.end()))
                break
    return sorted(candidates, key=lambda pair: (pair[0], -pair[1]))[0] if candidates else None

def _strip_presence_wrappers(value: str) -> str:
    value = value.strip()
    value = re.sub(r"^\s*[:;,.]+\s*", "", value)
    while len(value) >= 2 and ((value[0] == "[" and value[-1] == "]") or (value[0] == "(" and value[-1] == ")")):
        value = value[1:-1].strip()
    return value.strip(" ;,")


def _split_presence(text: str) -> list[tuple[str, str]]:
    """Return (text, presence_type) chunks."""
    # A few source strings carry a stray closing wrapper immediately before
    # the optional-ingredient marker, e.g. ``) May Contain: ...``.
    text = re.sub(r"^\s*[\]\)]\s*", "", text)
    boundary = _find_presence_boundary(text)
    if boundary is None:
        return [(text, "PRIMARY")]

    start, end = boundary
    primary = text[:start].strip(" ;,[]()")
    optional = text[end:]

    # The boundary regex consumes the marker and its immediate punctuation;
    # optional content may still be wrapped by the closing bracket from forms
    # such as ``[+/- A; B]``.
    optional = optional.strip()
    optional = re.sub(r"^[\s:;,]+", "", optional)
    optional = _strip_presence_wrappers(optional)

    chunks: list[tuple[str, str]] = []
    if primary:
        chunks.append((_strip_presence_wrappers(primary), "PRIMARY"))
    if optional:
        chunks.append((_strip_presence_wrappers(optional), "MAY_CONTAIN"))
    return chunks

def _logical_sections(elements: Iterable[str]) -> list[tuple[str, str]]:
    """Turn outer-list elements into (section, ingredient-stream) pairs."""
    section = "main"
    streams: list[tuple[str, str]] = []

    for element in elements:
        value = normalize_whitespace(element)
        if not value:
            continue

        # Standalone labels are always context.
        label = _section_label(value)
        if label:
            section = label
            continue

        # Explicit inline formulation labels are common in real data.
        inline_section, remainder = _split_inline_section(value)
        if inline_section:
            section = inline_section
            if remainder:
                streams.append((section, remainder))
            continue

        streams.append((section, value))

    return streams


def _extract_markers(raw: str) -> tuple[str, tuple[str, ...]]:
    markers: list[str] = []
    value = raw.strip()

    # Footnote suffix such as ``Limonene. *Antistatic agent...``.
    footnote = re.search(r"\.\s+[*+]{1,3}\s*", value)
    if footnote:
        value = value[:footnote.start()].rstrip(" .")
        markers.extend(re.findall(r"[*+]", footnote.group(0)))

    leading = re.match(r"^([*+]{1,3})\s*", value)
    if leading:
        markers.extend(list(leading.group(1)))
        value = value[leading.end():]

    attached = re.search(r"(?<=\w)([*+]{1,3})(?=\s*(?:\(|$|[.,]))", value)
    if attached:
        markers.extend(list(attached.group(1)))
        value = value[:attached.start()] + value[attached.end():]

    trailing = re.search(r"[*+]{1,3}\s*$", value)
    if trailing:
        markers.extend(list(trailing.group(0).strip()))
        value = value[:trailing.start()].rstrip()

    parenthetical_marker = re.search(r"\(\s*([*+]{1,3})(?:\s|[-])", value)
    if parenthetical_marker:
        markers.extend(list(parenthetical_marker.group(1)))

    return value, tuple(dict.fromkeys(markers))


def _extract_concentration(raw: str) -> tuple[str, float | None, str | None]:
    match = _PERCENT_RE.match(raw)
    if match:
        return raw[match.end():].strip(), float(match.group(1)), "%"

    match = _PERCENT_SUFFIX_RE.search(raw)
    if match:
        name = raw[:match.start()].strip()
        return name, float(match.group(1)), "%"

    return raw, None, None


def _remove_ci_parenthetical(value: str) -> str:
    """Remove a trailing parenthetical containing only CI color codes."""
    match = re.search(r"\(([^()]*)\)\s*$", value)
    if not match:
        return value
    inner = match.group(1)
    codes = [part.strip() for part in inner.split(",") if part.strip()]
    if codes and all(re.fullmatch(r"CI\s*\d{4,6}", code, re.I) for code in codes):
        return value[:match.start()].strip()
    return value


def _extract_ci_codes(raw: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(
        re.sub(r"\s+", " ", m.group(0)).upper()
        for m in _CI_RE.finditer(raw)
    ))




def _trim_unmatched_edge_delimiters(value: str) -> str:
    """Remove only delimiter characters that are unmatched at an edge.

    The source dataset contains a small number of malformed closing brackets.
    Balanced constructs such as ``[Nano]`` are preserved exactly.
    """
    value = value.strip()
    while value and value[0] in "}])" and value.count(value[0]) > value.count({")": "(", "]": "[", "}": "{"}[value[0]]):
        value = value[1:].lstrip()
    changed = True
    while changed and value:
        changed = False
        pairs = {")": "(", "]": "[", "}": "{"}
        if value[-1] in pairs and value.count(value[-1]) > value.count(pairs[value[-1]]):
            value = value[:-1].rstrip()
            changed = True
    return value


def parse_ingredients(product_id: str, raw: str | list[str] | tuple[str, ...]) -> list[IngredientRecord]:
    """Parse one product's raw ingredient field into structured records."""
    elements = parse_outer_list(raw)
    streams = _logical_sections(elements)

    records: list[IngredientRecord] = []
    position = 1

    for section, stream in streams:
        for presence_text, presence_type in _split_presence(stream):
            for token in split_top_level(presence_text, delimiters=",;"):
                token = token.strip()
                if not token:
                    continue

                if _section_label(token):
                    continue
                # Context markers such as ``(+/-)`` can occur as a standalone
                # token after a May Contain boundary. They are metadata, not
                # ingredients.
                if re.fullmatch(r"[\[\(\s]*(?:\+/-|±)[\]\)\s]*", token):
                    continue
                if re.fullmatch(r"[\[\s]*(?:may\s+contain|peut\s+contenir)(?:\s*/\s*(?:may\s+contain|peut\s+contenir))?[\]\s]*:?", token, re.I):
                    continue

                cleaned, markers = _extract_markers(token)
                cleaned, concentration, concentration_unit = _extract_concentration(cleaned)
                cleaned = normalize_whitespace(cleaned).strip(" ;,.:\t")
                cleaned = _trim_unmatched_edge_delimiters(cleaned)
                if not cleaned:
                    continue

                ci_codes = _extract_ci_codes(cleaned)
                cleaned = _remove_ci_parenthetical(cleaned)
                normalized = normalize_ingredient_name(cleaned)
                if not normalized:
                    continue

                records.append(
                    IngredientRecord(
                        product_id=str(product_id),
                        ingredient_raw=token,
                        ingredient_name=cleaned,
                        normalized_name=normalized,
                        position=position,
                        presence_type=presence_type,  # type: ignore[arg-type]
                        section=section,
                        concentration=concentration,
                        concentration_unit=concentration_unit,
                        ci_codes=ci_codes,
                        markers=markers,
                    )
                )
                position += 1

    return records


def parse_product_row(row) -> list[IngredientRecord]:
    return parse_ingredients(row["product_id"], row["ingredients"])
