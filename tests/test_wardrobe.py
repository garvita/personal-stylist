"""Tests for wardrobe management."""

import tempfile
from pathlib import Path

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


@pytest.fixture
def tmp_wardrobe(tmp_path):
    """Create a wardrobe with a temporary data directory."""
    return Wardrobe(data_dir=tmp_path)


@pytest.fixture
def populated_wardrobe(tmp_path):
    """Create a wardrobe pre-populated with sample items."""
    w = Wardrobe(data_dir=tmp_path)
    w.add_item(ClothingItem(
        name="White T-Shirt", category=Category.TOP, color=Color.WHITE,
        seasons=[Season.SPRING, Season.SUMMER],
        occasions=[Occasion.CASUAL],
    ))
    w.add_item(ClothingItem(
        name="Navy Blazer", category=Category.OUTERWEAR, color=Color.NAVY,
        seasons=[Season.SPRING, Season.FALL, Season.WINTER],
        occasions=[Occasion.BUSINESS, Occasion.FORMAL],
    ))
    w.add_item(ClothingItem(
        name="Blue Jeans", category=Category.BOTTOM, color=Color.BLUE,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
        occasions=[Occasion.CASUAL],
    ))
    w.add_item(ClothingItem(
        name="Black Sneakers", category=Category.SHOES, color=Color.BLACK,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
        occasions=[Occasion.CASUAL, Occasion.SPORT],
    ))
    w.add_item(ClothingItem(
        name="Black Dress", category=Category.DRESS, color=Color.BLACK,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
        occasions=[Occasion.FORMAL, Occasion.DATE],
    ))
    return w


class TestWardrobe:
    def test_add_item(self, tmp_wardrobe):
        item = ClothingItem(
            name="Red Scarf", category=Category.ACCESSORY, color=Color.RED,
            seasons=[Season.FALL, Season.WINTER],
            occasions=[Occasion.CASUAL],
        )
        added = tmp_wardrobe.add_item(item)
        assert added.id == item.id
        assert len(tmp_wardrobe.items) == 1

    def test_remove_item(self, populated_wardrobe):
        items = populated_wardrobe.items
        target_id = items[0].id
        removed = populated_wardrobe.remove_item(target_id)
        assert removed is not None
        assert removed.id == target_id
        assert len(populated_wardrobe.items) == len(items) - 1

    def test_remove_nonexistent(self, tmp_wardrobe):
        assert tmp_wardrobe.remove_item("nonexistent") is None

    def test_get_item(self, populated_wardrobe):
        items = populated_wardrobe.items
        found = populated_wardrobe.get_item(items[0].id)
        assert found is not None
        assert found.name == items[0].name

    def test_get_item_not_found(self, tmp_wardrobe):
        assert tmp_wardrobe.get_item("nope") is None

    def test_find_items_by_category(self, populated_wardrobe):
        tops = populated_wardrobe.find_items(category=Category.TOP)
        assert len(tops) == 1
        assert tops[0].name == "White T-Shirt"

    def test_find_items_by_color(self, populated_wardrobe):
        black_items = populated_wardrobe.find_items(color=Color.BLACK)
        assert len(black_items) == 2  # sneakers + dress

    def test_find_items_by_season(self, populated_wardrobe):
        summer_items = populated_wardrobe.find_items(season=Season.SUMMER)
        names = {i.name for i in summer_items}
        assert "White T-Shirt" in names
        assert "Navy Blazer" not in names

    def test_find_items_by_occasion(self, populated_wardrobe):
        formal = populated_wardrobe.find_items(occasion=Occasion.FORMAL)
        names = {i.name for i in formal}
        assert "Navy Blazer" in names
        assert "Black Dress" in names

    def test_list_by_category(self, populated_wardrobe):
        grouped = populated_wardrobe.list_by_category()
        assert Category.TOP in grouped
        assert len(grouped[Category.TOP]) == 1

    def test_stats(self, populated_wardrobe):
        st = populated_wardrobe.stats()
        assert st["total"] == 5
        assert st[Category.TOP] == 1
        assert st[Category.SHOES] == 1

    def test_persistence(self, tmp_path):
        w1 = Wardrobe(data_dir=tmp_path)
        w1.add_item(ClothingItem(
            name="Test Item", category=Category.TOP, color=Color.RED,
            seasons=[Season.SPRING], occasions=[Occasion.CASUAL],
            id="persist1",
        ))
        # Load from same directory
        w2 = Wardrobe(data_dir=tmp_path)
        assert len(w2.items) == 1
        assert w2.items[0].id == "persist1"

    def test_profile_persistence(self, tmp_path):
        w1 = Wardrobe(data_dir=tmp_path)
        w1.set_profile(UserProfile(
            name="Test User",
            preferred_colors=[Color.BLUE],
        ))
        w2 = Wardrobe(data_dir=tmp_path)
        assert w2.profile is not None
        assert w2.profile.name == "Test User"
