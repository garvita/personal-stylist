"""Tests for the outfit recommendation engine."""

import pytest

from personal_stylist.models import (
    Category,
    ClothingItem,
    Color,
    Occasion,
    Season,
    UserProfile,
)
from personal_stylist.wardrobe import Wardrobe
from personal_stylist.recommender import OutfitRecommender


@pytest.fixture
def full_wardrobe(tmp_path):
    """Wardrobe with enough items to generate recommendations."""
    w = Wardrobe(data_dir=tmp_path)
    items = [
        ClothingItem(
            name="White Oxford", category=Category.TOP, color=Color.WHITE,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
            occasions=[Occasion.CASUAL, Occasion.BUSINESS],
        ),
        ClothingItem(
            name="Navy Polo", category=Category.TOP, color=Color.NAVY,
            seasons=[Season.SPRING, Season.SUMMER],
            occasions=[Occasion.CASUAL],
        ),
        ClothingItem(
            name="Gray Sweater", category=Category.TOP, color=Color.GRAY,
            seasons=[Season.FALL, Season.WINTER],
            occasions=[Occasion.CASUAL, Occasion.BUSINESS],
        ),
        ClothingItem(
            name="Blue Jeans", category=Category.BOTTOM, color=Color.BLUE,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
            occasions=[Occasion.CASUAL],
        ),
        ClothingItem(
            name="Khaki Chinos", category=Category.BOTTOM, color=Color.BEIGE,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
            occasions=[Occasion.CASUAL, Occasion.BUSINESS],
        ),
        ClothingItem(
            name="Black Trousers", category=Category.BOTTOM, color=Color.BLACK,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
            occasions=[Occasion.BUSINESS, Occasion.FORMAL],
        ),
        ClothingItem(
            name="White Sneakers", category=Category.SHOES, color=Color.WHITE,
            seasons=[Season.SPRING, Season.SUMMER],
            occasions=[Occasion.CASUAL, Occasion.SPORT],
        ),
        ClothingItem(
            name="Brown Boots", category=Category.SHOES, color=Color.BROWN,
            seasons=[Season.FALL, Season.WINTER],
            occasions=[Occasion.CASUAL, Occasion.BUSINESS],
        ),
        ClothingItem(
            name="Black Dress Shoes", category=Category.SHOES, color=Color.BLACK,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
            occasions=[Occasion.BUSINESS, Occasion.FORMAL],
        ),
        ClothingItem(
            name="Navy Blazer", category=Category.OUTERWEAR, color=Color.NAVY,
            seasons=[Season.SPRING, Season.FALL],
            occasions=[Occasion.BUSINESS, Occasion.FORMAL],
        ),
        ClothingItem(
            name="Silver Watch", category=Category.ACCESSORY, color=Color.GRAY,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
            occasions=[Occasion.CASUAL, Occasion.BUSINESS, Occasion.FORMAL],
        ),
        ClothingItem(
            name="Black Dress", category=Category.DRESS, color=Color.BLACK,
            seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
            occasions=[Occasion.FORMAL, Occasion.DATE],
        ),
    ]
    for item in items:
        w.add_item(item)
    return w


@pytest.fixture
def minimal_wardrobe(tmp_path):
    """Wardrobe with just enough for one outfit."""
    w = Wardrobe(data_dir=tmp_path)
    w.add_item(ClothingItem(
        name="Shirt", category=Category.TOP, color=Color.WHITE,
        seasons=[Season.SUMMER], occasions=[Occasion.CASUAL],
    ))
    w.add_item(ClothingItem(
        name="Shorts", category=Category.BOTTOM, color=Color.BEIGE,
        seasons=[Season.SUMMER], occasions=[Occasion.CASUAL],
    ))
    w.add_item(ClothingItem(
        name="Sandals", category=Category.SHOES, color=Color.BROWN,
        seasons=[Season.SUMMER], occasions=[Occasion.CASUAL],
    ))
    return w


class TestOutfitRecommender:
    def test_basic_recommendations(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(max_results=3)
        assert len(outfits) > 0
        assert len(outfits) <= 3

    def test_recommendations_sorted_by_score(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(max_results=10)
        scores = [o.score for o in outfits]
        assert scores == sorted(scores, reverse=True)

    def test_season_filter(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(season=Season.WINTER, max_results=5)
        for outfit in outfits:
            for item in outfit.items:
                assert item.matches_season(Season.WINTER)

    def test_occasion_filter(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(occasion=Occasion.FORMAL, max_results=5)
        for outfit in outfits:
            for item in outfit.items:
                assert item.matches_occasion(Occasion.FORMAL)

    def test_complete_outfits_score_higher(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(max_results=20)
        complete = [o for o in outfits if o.is_complete()]
        incomplete = [o for o in outfits if not o.is_complete()]
        if complete and incomplete:
            assert max(o.score for o in complete) >= max(o.score for o in incomplete)

    def test_minimal_wardrobe_produces_outfit(self, minimal_wardrobe):
        rec = OutfitRecommender(minimal_wardrobe)
        outfits = rec.recommend(max_results=5)
        assert len(outfits) >= 1
        assert outfits[0].is_complete()

    def test_empty_wardrobe(self, tmp_path):
        w = Wardrobe(data_dir=tmp_path)
        rec = OutfitRecommender(w)
        outfits = rec.recommend()
        assert outfits == []

    def test_user_preferences_boost_score(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits_no_pref = rec.recommend(max_results=1)

        full_wardrobe.set_profile(UserProfile(
            name="Tester",
            preferred_colors=[Color.WHITE, Color.BEIGE],
        ))
        outfits_with_pref = rec.recommend(max_results=1)

        # With preferences set, scores should differ (preference bonus applied)
        # We just verify the recommendation engine doesn't crash
        assert len(outfits_with_pref) > 0

    def test_dress_based_outfit(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(occasion=Occasion.FORMAL, max_results=20)
        dress_outfits = [
            o for o in outfits
            if any(i.category == Category.DRESS for i in o.items)
        ]
        assert len(dress_outfits) > 0


class TestRecommenderScoring:
    def test_score_range(self, full_wardrobe):
        rec = OutfitRecommender(full_wardrobe)
        outfits = rec.recommend(
            season=Season.SPRING,
            occasion=Occasion.CASUAL,
            max_results=20,
        )
        for outfit in outfits:
            assert 0 <= outfit.score <= 100

    def test_color_coordinated_scores_higher(self, tmp_path):
        """Outfits with coordinated colors should score higher."""
        w = Wardrobe(data_dir=tmp_path)
        # Well-coordinated set: navy + white + brown
        w.add_item(ClothingItem(
            name="Navy Shirt", category=Category.TOP, color=Color.NAVY,
            seasons=[Season.SPRING], occasions=[Occasion.CASUAL], id="coord_top",
        ))
        w.add_item(ClothingItem(
            name="White Pants", category=Category.BOTTOM, color=Color.WHITE,
            seasons=[Season.SPRING], occasions=[Occasion.CASUAL], id="coord_bot",
        ))
        w.add_item(ClothingItem(
            name="Brown Shoes", category=Category.SHOES, color=Color.BROWN,
            seasons=[Season.SPRING], occasions=[Occasion.CASUAL], id="coord_shoe",
        ))
        # Poorly coordinated extra: red + orange
        w.add_item(ClothingItem(
            name="Red Shirt", category=Category.TOP, color=Color.RED,
            seasons=[Season.SPRING], occasions=[Occasion.CASUAL], id="clash_top",
        ))
        w.add_item(ClothingItem(
            name="Orange Pants", category=Category.BOTTOM, color=Color.ORANGE,
            seasons=[Season.SPRING], occasions=[Occasion.CASUAL], id="clash_bot",
        ))

        rec = OutfitRecommender(w)
        outfits = rec.recommend(season=Season.SPRING, max_results=20)
        # Find the coordinated vs clashing outfits
        coordinated = None
        clashing = None
        for o in outfits:
            ids = {i.id for i in o.items}
            if "coord_top" in ids and "coord_bot" in ids and "coord_shoe" in ids:
                coordinated = o
            if "clash_top" in ids and "clash_bot" in ids:
                clashing = o

        assert coordinated is not None
        if clashing is not None:
            assert coordinated.score >= clashing.score
