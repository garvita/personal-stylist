"""Tests for the Flask web application."""

import io
from pathlib import Path

import pytest

from personal_stylist.analyzer import analyze_colors_mock
from personal_stylist.models import (
    Category, ClothingItem, Color, ColorAnalysis, Occasion, Season, UserProfile,
)
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

    def test_add_item_with_image(self, client):
        data = {
            "category": "top",
            "image": (io.BytesIO(b"\xff\xd8\xff fake jpeg"), "blue_shirt.jpg"),
        }
        resp = client.post(
            "/add", data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Added Blue Shirt" in resp.data

    def test_add_item_missing_image(self, client):
        resp = client.post("/add", data={
            "category": "top",
        }, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_add_item_missing_category(self, client):
        data = {
            "category": "",
            "image": (io.BytesIO(b"\xff\xd8\xff fake jpeg"), "shirt.jpg"),
        }
        resp = client.post(
            "/add", data=data,
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        assert b"required" in resp.data

    def test_name_derived_from_filename(self, client):
        data = {
            "category": "shoes",
            "image": (io.BytesIO(b"\xff\xd8\xff fake"), "red_running-shoes.jpg"),
        }
        resp = client.post(
            "/add", data=data,
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Red Running Shoes" in resp.data


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


class TestProfilePhotos:
    def test_upload_photo(self, tmp_path):
        app = create_app(data_dir=tmp_path)
        app.config["TESTING"] = True
        client = app.test_client()
        # Set up profile first
        client.post("/profile", data={"name": "Tester"}, follow_redirects=True)
        resp = client.post(
            "/profile/upload-photos",
            data={"photos": (io.BytesIO(b"\xff\xd8\xff fake"), "face.jpg")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Uploaded 1 photo" in resp.data

    def test_upload_multiple_photos(self, tmp_path):
        app = create_app(data_dir=tmp_path)
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/profile", data={"name": "Tester"}, follow_redirects=True)
        resp = client.post(
            "/profile/upload-photos",
            data={
                "photos": [
                    (io.BytesIO(b"\xff\xd8\xff"), "a.jpg"),
                    (io.BytesIO(b"\xff\xd8\xff"), "b.jpg"),
                ],
            },
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Uploaded 2 photos" in resp.data

    def test_upload_no_files(self, client):
        resp = client.post(
            "/profile/upload-photos",
            data={},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"select at least one photo" in resp.data

    def test_clear_photos(self, tmp_path):
        app = create_app(data_dir=tmp_path)
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/profile", data={"name": "Tester"}, follow_redirects=True)
        client.post(
            "/profile/upload-photos",
            data={"photos": (io.BytesIO(b"\xff\xd8\xff"), "face.jpg")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        resp = client.post("/profile/clear-photos", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Removed 1 photo" in resp.data

    def test_clear_no_photos(self, client):
        resp = client.post("/profile/clear-photos", follow_redirects=True)
        assert resp.status_code == 200
        assert b"No photos to remove" in resp.data


class TestColorAnalysis:
    def _setup_with_photos(self, tmp_path):
        app = create_app(data_dir=tmp_path, analyzer_func=analyze_colors_mock)
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/profile", data={"name": "Tester"}, follow_redirects=True)
        client.post(
            "/profile/upload-photos",
            data={"photos": (io.BytesIO(b"\xff\xd8\xff fake"), "face.jpg")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        return client

    def test_analyze_with_mock(self, tmp_path):
        client = self._setup_with_photos(tmp_path)
        resp = client.post(
            "/profile/analyze",
            data={"use_mock": "1"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Color analysis complete" in resp.data
        assert b"Soft Autumn" in resp.data

    def test_analyze_shows_palette(self, tmp_path):
        client = self._setup_with_photos(tmp_path)
        client.post("/profile/analyze", data={"use_mock": "1"}, follow_redirects=True)
        resp = client.get("/profile")
        assert resp.status_code == 200
        assert b"Your Best Colors" in resp.data
        assert b"Colors to Avoid" in resp.data
        assert b"Best Metals" in resp.data

    def test_analyze_shows_season(self, tmp_path):
        client = self._setup_with_photos(tmp_path)
        client.post("/profile/analyze", data={"use_mock": "1"}, follow_redirects=True)
        resp = client.get("/profile")
        assert b"Undertone" in resp.data
        assert b"Confidence" in resp.data

    def test_analyze_no_photos(self, client):
        resp = client.post(
            "/profile/analyze",
            data={"use_mock": "1"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Upload at least one photo" in resp.data

    def test_analyze_no_api_key(self, tmp_path, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        app = create_app(data_dir=tmp_path)
        app.config["TESTING"] = True
        client = app.test_client()
        client.post("/profile", data={"name": "Tester"}, follow_redirects=True)
        client.post(
            "/profile/upload-photos",
            data={"photos": (io.BytesIO(b"\xff\xd8\xff"), "face.jpg")},
            content_type="multipart/form-data",
            follow_redirects=True,
        )
        resp = client.post(
            "/profile/analyze",
            data={"use_mock": "0"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"ANTHROPIC_API_KEY" in resp.data

    def test_profile_preserves_analysis_on_update(self, tmp_path):
        client = self._setup_with_photos(tmp_path)
        client.post("/profile/analyze", data={"use_mock": "1"}, follow_redirects=True)
        # Update profile preferences
        client.post("/profile", data={
            "name": "Updated",
            "preferred_colors": ["navy"],
        }, follow_redirects=True)
        resp = client.get("/profile")
        assert b"Updated" in resp.data
        assert b"Soft Autumn" in resp.data  # analysis preserved
