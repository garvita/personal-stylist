"""Tests for the Flask web application."""

import io
from pathlib import Path

import pytest

from personal_stylist.models import Category, ClothingItem, Color, Occasion, Season
from personal_stylist.wardrobe import Wardrobe
from personal_stylist.webapp import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app(data_dir=tmp_path)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def populated_app(tmp_path):
    """App with some items pre-loaded."""
    w = Wardrobe(data_dir=tmp_path)
    w.add_item(ClothingItem(
        name="White Tee", category=Category.TOP, color=Color.WHITE,
        seasons=[Season.SPRING, Season.SUMMER],
        occasions=[Occasion.CASUAL], id="wtee",
    ))
    w.add_item(ClothingItem(
        name="Blue Jeans", category=Category.BOTTOM, color=Color.BLUE,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL],
        occasions=[Occasion.CASUAL], id="bjeans",
    ))
    w.add_item(ClothingItem(
        name="Sneakers", category=Category.SHOES, color=Color.WHITE,
        seasons=[Season.SPRING, Season.SUMMER, Season.FALL, Season.WINTER],
        occasions=[Occasion.CASUAL, Occasion.SPORT], id="snkrs",
    ))
    app = create_app(data_dir=tmp_path)
    app.config["TESTING"] = True
    return app


@pytest.fixture
def populated_client(populated_app):
    return populated_app.test_client()


class TestIndex:
    def test_empty_wardrobe(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Your wardrobe is empty" in resp.data

    def test_with_items(self, populated_client):
        resp = populated_client.get("/")
        assert resp.status_code == 200
        assert b"White Tee" in resp.data
        assert b"Blue Jeans" in resp.data
        assert b"Sneakers" in resp.data

    def test_stats_shown(self, populated_client):
        resp = populated_client.get("/")
        assert resp.status_code == 200
        assert b"3 items" in resp.data


class TestAddItem:
    def test_get_form(self, client):
        resp = client.get("/add")
        assert resp.status_code == 200
        assert b"Add to Wardrobe" in resp.data

    def test_add_item_post(self, client):
        resp = client.post("/add", data={
            "name": "Red Scarf",
            "category": "accessory",
            "color": "red",
            "seasons": ["fall", "winter"],
            "occasions": ["casual"],
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Added Red Scarf" in resp.data
        assert b"Red Scarf" in resp.data

    def test_add_item_missing_name(self, client):
        resp = client.post("/add", data={
            "name": "",
            "category": "top",
            "color": "blue",
        })
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_add_item_with_image(self, client):
        data = {
            "name": "Photo Shirt",
            "category": "top",
            "color": "blue",
            "seasons": ["summer"],
            "occasions": ["casual"],
            "image": (io.BytesIO(b"\xff\xd8\xff fake jpeg"), "shirt.jpg"),
        }
        resp = client.post(
            "/add", data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Added Photo Shirt" in resp.data

    def test_add_defaults_seasons_occasions(self, client):
        resp = client.post("/add", data={
            "name": "Basic Top",
            "category": "top",
            "color": "black",
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Added Basic Top" in resp.data


class TestRemoveItem:
    def test_remove(self, populated_client):
        resp = populated_client.post("/remove/wtee", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Removed White Tee" in resp.data
        # Verify it's gone
        resp2 = populated_client.get("/")
        assert b"White Tee" not in resp2.data

    def test_remove_nonexistent(self, client):
        resp = client.post("/remove/bogus", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Item not found" in resp.data


class TestRecommend:
    def test_empty_wardrobe(self, client):
        resp = client.get("/recommend")
        assert resp.status_code == 200
        assert b"No outfits to recommend" in resp.data

    def test_with_items(self, populated_client):
        resp = populated_client.get("/recommend")
        assert resp.status_code == 200
        assert b"Outfit 1" in resp.data
        assert b"/ 100" in resp.data

    def test_filter_by_season(self, populated_client):
        resp = populated_client.get("/recommend?season=summer")
        assert resp.status_code == 200
        assert b"Outfit" in resp.data

    def test_filter_by_occasion(self, populated_client):
        resp = populated_client.get("/recommend?occasion=casual")
        assert resp.status_code == 200
        assert b"Outfit" in resp.data


class TestProfile:
    def test_get_empty_profile(self, client):
        resp = client.get("/profile")
        assert resp.status_code == 200
        assert b"Style Profile" in resp.data

    def test_save_profile(self, client):
        resp = client.post("/profile", data={
            "name": "Alice",
            "preferred_colors": ["navy", "black"],
            "preferred_occasions": ["business"],
            "preferred_seasons": ["fall"],
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"Profile updated for Alice" in resp.data

    def test_profile_persists(self, client):
        client.post("/profile", data={
            "name": "Bob",
            "preferred_colors": ["blue"],
        }, follow_redirects=True)
        resp = client.get("/profile")
        assert b"Bob" in resp.data
