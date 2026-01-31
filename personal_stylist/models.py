"""Data models for the personal stylist application."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional


class Category(str, Enum):
    """Clothing categories."""
    TOP = "top"
    BOTTOM = "bottom"
    DRESS = "dress"
    OUTERWEAR = "outerwear"
    SHOES = "shoes"
    ACCESSORY = "accessory"


class Season(str, Enum):
    """Seasons for clothing suitability."""
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


class Occasion(str, Enum):
    """Occasions for outfit recommendations."""
    CASUAL = "casual"
    BUSINESS = "business"
    FORMAL = "formal"
    SPORT = "sport"
    DATE = "date"
    OUTDOOR = "outdoor"


class Color(str, Enum):
    """Standard clothing colors."""
    BLACK = "black"
    WHITE = "white"
    GRAY = "gray"
    NAVY = "navy"
    BLUE = "blue"
    RED = "red"
    GREEN = "green"
    BROWN = "brown"
    BEIGE = "beige"
    PINK = "pink"
    YELLOW = "yellow"
    ORANGE = "orange"
    PURPLE = "purple"
    OLIVE = "olive"
    BURGUNDY = "burgundy"
    TEAL = "teal"


# Color coordination rules: maps a color to colors that pair well with it
COLOR_COMPLEMENTS: dict[str, set[str]] = {
    Color.BLACK: {Color.WHITE, Color.RED, Color.PINK, Color.GRAY, Color.BEIGE, Color.NAVY, Color.BLUE, Color.YELLOW, Color.BURGUNDY, Color.TEAL},
    Color.WHITE: {Color.BLACK, Color.NAVY, Color.BLUE, Color.RED, Color.GREEN, Color.BEIGE, Color.GRAY, Color.BROWN, Color.PINK, Color.TEAL, Color.BURGUNDY},
    Color.GRAY: {Color.BLACK, Color.WHITE, Color.BLUE, Color.NAVY, Color.PINK, Color.RED, Color.PURPLE, Color.TEAL, Color.BURGUNDY},
    Color.NAVY: {Color.WHITE, Color.BEIGE, Color.GRAY, Color.BROWN, Color.PINK, Color.RED, Color.YELLOW, Color.ORANGE, Color.BURGUNDY},
    Color.BLUE: {Color.WHITE, Color.GRAY, Color.BEIGE, Color.BROWN, Color.NAVY, Color.BLACK, Color.YELLOW, Color.ORANGE},
    Color.RED: {Color.BLACK, Color.WHITE, Color.GRAY, Color.NAVY, Color.BEIGE, Color.BLUE},
    Color.GREEN: {Color.WHITE, Color.BEIGE, Color.BROWN, Color.BLACK, Color.GRAY, Color.NAVY},
    Color.BROWN: {Color.WHITE, Color.BEIGE, Color.BLUE, Color.GREEN, Color.NAVY, Color.ORANGE, Color.OLIVE},
    Color.BEIGE: {Color.BLACK, Color.WHITE, Color.NAVY, Color.BROWN, Color.BLUE, Color.GREEN, Color.BURGUNDY, Color.OLIVE},
    Color.PINK: {Color.BLACK, Color.WHITE, Color.GRAY, Color.NAVY, Color.BLUE, Color.BEIGE},
    Color.YELLOW: {Color.BLACK, Color.NAVY, Color.BLUE, Color.GRAY, Color.WHITE, Color.BROWN},
    Color.ORANGE: {Color.NAVY, Color.BLUE, Color.WHITE, Color.BROWN, Color.BLACK, Color.BEIGE},
    Color.PURPLE: {Color.WHITE, Color.GRAY, Color.BLACK, Color.BEIGE, Color.PINK, Color.NAVY},
    Color.OLIVE: {Color.WHITE, Color.BEIGE, Color.BROWN, Color.BLACK, Color.NAVY, Color.BURGUNDY},
    Color.BURGUNDY: {Color.WHITE, Color.BEIGE, Color.GRAY, Color.BLACK, Color.NAVY, Color.PINK, Color.OLIVE},
    Color.TEAL: {Color.WHITE, Color.BEIGE, Color.GRAY, Color.BLACK, Color.NAVY, Color.BROWN},
}


def colors_coordinate(c1: str, c2: str) -> bool:
    """Check if two colors coordinate well together."""
    if c1 == c2:
        return True
    complements = COLOR_COMPLEMENTS.get(c1, set())
    return c2 in complements


@dataclass
class ClothingItem:
    """Represents a single clothing item in the wardrobe."""
    name: str
    category: str
    color: str
    seasons: list[str]
    occasions: list[str]
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    image_path: Optional[str] = None

    def matches_season(self, season: str) -> bool:
        return season in self.seasons

    def matches_occasion(self, occasion: str) -> bool:
        return occasion in self.occasions

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> ClothingItem:
        return cls(**data)


@dataclass
class Outfit:
    """A combination of clothing items forming a complete outfit."""
    items: list[ClothingItem]
    score: float = 0.0

    @property
    def categories_present(self) -> set[str]:
        return {item.category for item in self.items}

    def has_category(self, category: str) -> bool:
        return category in self.categories_present

    def is_complete(self) -> bool:
        """An outfit needs at least a top+bottom or a dress, plus shoes."""
        has_dress = self.has_category(Category.DRESS)
        has_top_and_bottom = (
            self.has_category(Category.TOP) and self.has_category(Category.BOTTOM)
        )
        has_shoes = self.has_category(Category.SHOES)
        return (has_dress or has_top_and_bottom) and has_shoes

    def describe(self) -> str:
        lines = []
        for item in self.items:
            lines.append(f"  - {item.name} ({item.color} {item.category})")
        score_str = f"  Score: {self.score:.1f}/100"
        return "\n".join(lines) + "\n" + score_str


@dataclass
class UserProfile:
    """User style preferences."""
    name: str
    preferred_colors: list[str] = field(default_factory=list)
    preferred_occasions: list[str] = field(default_factory=list)
    preferred_seasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> UserProfile:
        return cls(**data)
