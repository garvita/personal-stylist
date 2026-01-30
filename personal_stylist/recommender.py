"""Outfit recommendation engine.

Generates outfit combinations from the wardrobe and scores them based on:
- Color coordination between items
- Seasonal appropriateness
- Occasion matching
- User style preferences
- Outfit completeness
"""

from __future__ import annotations

import itertools
import random
from typing import Optional

from personal_stylist.models import (
    Category,
    ClothingItem,
    Outfit,
    UserProfile,
    colors_coordinate,
)
from personal_stylist.wardrobe import Wardrobe


class OutfitRecommender:
    """Generates and scores outfit recommendations from a wardrobe."""

    def __init__(self, wardrobe: Wardrobe):
        self.wardrobe = wardrobe

    def recommend(
        self,
        season: Optional[str] = None,
        occasion: Optional[str] = None,
        max_results: int = 5,
    ) -> list[Outfit]:
        """Generate outfit recommendations sorted by score (highest first).

        Args:
            season: Filter items by season suitability.
            occasion: Filter items by occasion suitability.
            max_results: Maximum number of outfits to return.

        Returns:
            List of Outfit objects sorted by descending score.
        """
        candidates = self._generate_candidates(season, occasion)
        scored = []
        for outfit in candidates:
            outfit.score = self._score_outfit(outfit, season, occasion)
            scored.append(outfit)

        scored.sort(key=lambda o: o.score, reverse=True)
        return scored[:max_results]

    def _generate_candidates(
        self,
        season: Optional[str] = None,
        occasion: Optional[str] = None,
    ) -> list[Outfit]:
        """Build candidate outfits from wardrobe items."""
        items = self.wardrobe.items
        if season:
            items = [i for i in items if i.matches_season(season)]
        if occasion:
            items = [i for i in items if i.matches_occasion(occasion)]

        by_category: dict[str, list[ClothingItem]] = {}
        for item in items:
            by_category.setdefault(item.category, []).append(item)

        outfits: list[Outfit] = []

        # Strategy 1: top + bottom + shoes (+ optional outerwear/accessory)
        tops = by_category.get(Category.TOP, [])
        bottoms = by_category.get(Category.BOTTOM, [])
        shoes = by_category.get(Category.SHOES, [])
        outerwear = by_category.get(Category.OUTERWEAR, [])
        accessories = by_category.get(Category.ACCESSORY, [])

        if tops and bottoms and shoes:
            combos = list(itertools.product(tops, bottoms, shoes))
            # Limit combinatorial explosion
            if len(combos) > 200:
                combos = random.sample(combos, 200)
            for top, bottom, shoe in combos:
                base = [top, bottom, shoe]
                outfits.append(Outfit(items=list(base)))
                # Add outerwear variants
                for outer in outerwear[:3]:
                    outfits.append(Outfit(items=base + [outer]))
                # Add accessory variants
                for acc in accessories[:3]:
                    outfits.append(Outfit(items=base + [acc]))

        # Strategy 2: dress + shoes (+ optional outerwear/accessory)
        dresses = by_category.get(Category.DRESS, [])
        if dresses and shoes:
            for dress, shoe in itertools.product(dresses, shoes):
                base = [dress, shoe]
                outfits.append(Outfit(items=list(base)))
                for outer in outerwear[:3]:
                    outfits.append(Outfit(items=base + [outer]))
                for acc in accessories[:3]:
                    outfits.append(Outfit(items=base + [acc]))

        return outfits

    def _score_outfit(
        self,
        outfit: Outfit,
        season: Optional[str] = None,
        occasion: Optional[str] = None,
    ) -> float:
        """Score an outfit from 0-100 based on multiple criteria."""
        score = 0.0
        items = outfit.items

        # 1. Completeness (0-30 points)
        if outfit.is_complete():
            score += 25.0
            if outfit.has_category(Category.ACCESSORY):
                score += 3.0
            if outfit.has_category(Category.OUTERWEAR):
                score += 2.0

        # 2. Color coordination (0-35 points)
        score += self._score_color_coordination(items) * 35.0

        # 3. Season match (0-15 points)
        if season:
            matching = sum(1 for i in items if i.matches_season(season))
            score += (matching / len(items)) * 15.0

        # 4. Occasion match (0-15 points)
        if occasion:
            matching = sum(1 for i in items if i.matches_occasion(occasion))
            score += (matching / len(items)) * 15.0

        # 5. User preference bonus (0-5 points)
        profile = self.wardrobe.profile
        if profile and profile.preferred_colors:
            pref_match = sum(
                1 for i in items if i.color in profile.preferred_colors
            )
            score += (pref_match / len(items)) * 5.0

        return min(score, 100.0)

    def _score_color_coordination(self, items: list[ClothingItem]) -> float:
        """Score how well item colors coordinate (0.0 to 1.0)."""
        if len(items) < 2:
            return 1.0

        pairs = list(itertools.combinations(items, 2))
        coordinated = sum(
            1 for a, b in pairs if colors_coordinate(a.color, b.color)
        )
        return coordinated / len(pairs)
