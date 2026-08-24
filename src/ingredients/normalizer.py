from __future__ import annotations

import re


_PERCENT_PREFIX = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*%\s*")
_MARKER_RE = re.compile(r"^[*\s]+|[*\s]+$")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalize_ingredient_name(value: str) -> str:
    """Conservative canonicalization.

    We intentionally do NOT perform chemical synonym mapping yet. That belongs
    to the later ingredient knowledge layer and should be backed by an explicit
    ontology rather than guessed here.
    """
    value = normalize_whitespace(value)
    value = _PERCENT_PREFIX.sub("", value)
    value = value.strip(" ;,:")
    value = _MARKER_RE.sub("", value)
    return normalize_whitespace(value).casefold()
