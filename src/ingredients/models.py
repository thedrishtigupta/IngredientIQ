from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PresenceType = Literal["PRIMARY", "MAY_CONTAIN"]


@dataclass(frozen=True)
class IngredientRecord:
    """One parsed ingredient occurrence in a product formulation."""

    product_id: str
    ingredient_raw: str
    ingredient_name: str
    normalized_name: str
    position: int
    presence_type: PresenceType = "PRIMARY"
    section: str = "main"
    concentration: float | None = None
    concentration_unit: str | None = None
    ci_codes: tuple[str, ...] = field(default_factory=tuple)
    markers: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "product_id": self.product_id,
            "ingredient_raw": self.ingredient_raw,
            "ingredient_name": self.ingredient_name,
            "normalized_name": self.normalized_name,
            "position": self.position,
            "presence_type": self.presence_type,
            "section": self.section,
            "concentration": self.concentration,
            "concentration_unit": self.concentration_unit,
            "ci_codes": list(self.ci_codes),
            "markers": list(self.markers),
        }
