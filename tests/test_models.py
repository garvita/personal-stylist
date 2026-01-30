"""Tests for data models."""

from personal_stylist.models import (
    Category,
    ClothingItem,
    Color,
    Occasion,
    Outfit,
    Season,
    UserProfile,
    colors_coordinate,
)


class TestClothingItem:
    def test_create_item(self):
        item = ClothingItem(
            name="Blue Shirt",
            category=Category.TOP,
            color=Color.BLUE,
            seasons=[Season.SPRING, Season.SUMMER],
            occasions=[Occasion.CASUAL, Occasion.BUSINESS],
        )
        assert item.name == "Blue Shirt"
        assert item.category == Category.TOP
        assert item.color == Color.BLUE
        assert len(item.id) == 8

    def test_matches_season(self):
        item = ClothingItem(
            name="Sweater",
            category=Category.TOP,
            color=Color.GRAY,
            seasons=[Season.FALL, Season.WINTER],
            occasions=[Occasion.CASUAL],
        )
        assert item.matches_season(Season.WINTER)
        assert not item.matches_season(Season.SUMMER)

    def test_matches_occasion(self):
        item = ClothingItem(
            name="Suit Jacket",
            category=Category.OUTERWEAR,
            color=Color.NAVY,
            seasons=[Season.SPRING, Season.FALL, Season.WINTER],
            occasions=[Occasion.BUSINESS, Occasion.FORMAL],
        )
        assert item.matches_occasion(Occasion.FORMAL)
        assert not item.matches_occasion(Occasion.SPORT)

    def test_to_dict_and_from_dict(self):
        item = ClothingItem(
            name="Jeans",
            category=Category.BOTTOM,
            color=Color.BLUE,
            seasons=[Season.SPRING, Season.FALL],
            occasions=[Occasion.CASUAL],
            id="abc12345",
        )
        d = item.to_dict()
        restored = ClothingItem.from_dict(d)
        assert restored.name == item.name
        assert restored.category == item.category
        assert restored.color == item.color
        assert restored.seasons == item.seasons
        assert restored.occasions == item.occasions
        assert restored.id == item.id


class TestColorCoordination:
    def test_same_color_coordinates(self):
        assert colors_coordinate(Color.BLACK, Color.BLACK)

    def test_classic_pair(self):
        assert colors_coordinate(Color.BLACK, Color.WHITE)
        assert colors_coordinate(Color.NAVY, Color.WHITE)

    def test_non_matching(self):
        assert not colors_coordinate(Color.RED, Color.ORANGE)
        assert not colors_coordinate(Color.GREEN, Color.RED)


class TestOutfit:
    def _make_item(self, category, color=Color.BLACK):
        return ClothingItem(
            name=f"Test {category}",
            category=category,
            color=color,
            seasons=[Season.SPRING],
            occasions=[Occasion.CASUAL],
        )

    def test_complete_outfit_top_bottom_shoes(self):
        outfit = Outfit(items=[
            self._make_item(Category.TOP),
            self._make_item(Category.BOTTOM),
            self._make_item(Category.SHOES),
        ])
        assert outfit.is_complete()

    def test_complete_outfit_dress_shoes(self):
        outfit = Outfit(items=[
            self._make_item(Category.DRESS),
            self._make_item(Category.SHOES),
        ])
        assert outfit.is_complete()

    def test_incomplete_outfit_missing_shoes(self):
        outfit = Outfit(items=[
            self._make_item(Category.TOP),
            self._make_item(Category.BOTTOM),
        ])
        assert not outfit.is_complete()

    def test_incomplete_outfit_top_only(self):
        outfit = Outfit(items=[
            self._make_item(Category.TOP),
            self._make_item(Category.SHOES),
        ])
        assert not outfit.is_complete()

    def test_categories_present(self):
        outfit = Outfit(items=[
            self._make_item(Category.TOP),
            self._make_item(Category.BOTTOM),
            self._make_item(Category.SHOES),
            self._make_item(Category.ACCESSORY),
        ])
        assert outfit.categories_present == {
            Category.TOP, Category.BOTTOM, Category.SHOES, Category.ACCESSORY,
        }

    def test_describe(self):
        outfit = Outfit(
            items=[
                self._make_item(Category.TOP, Color.WHITE),
                self._make_item(Category.BOTTOM, Color.NAVY),
            ],
            score=75.5,
        )
        desc = outfit.describe()
        assert "white" in desc.lower()
        assert "75.5" in desc


class TestUserProfile:
    def test_create_profile(self):
        profile = UserProfile(
            name="Alice",
            preferred_colors=[Color.NAVY, Color.BLACK],
            preferred_occasions=[Occasion.BUSINESS],
        )
        assert profile.name == "Alice"
        assert Color.NAVY in profile.preferred_colors

    def test_round_trip(self):
        profile = UserProfile(
            name="Bob",
            preferred_colors=[Color.BLUE],
            preferred_occasions=[Occasion.CASUAL],
            preferred_seasons=[Season.SUMMER],
        )
        d = profile.to_dict()
        restored = UserProfile.from_dict(d)
        assert restored.name == profile.name
        assert restored.preferred_colors == profile.preferred_colors
