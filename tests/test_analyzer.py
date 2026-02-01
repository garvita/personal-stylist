"""Tests for the color analysis module."""

import pytest

from personal_stylist.analyzer import analyze_colors_mock, _load_image_as_base64
from personal_stylist.models import ColorAnalysis


class TestAnalyzeColorsMock:
    def test_returns_color_analysis(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert isinstance(result, ColorAnalysis)

    def test_has_season(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert result.season != ""
        assert result.sub_season != ""

    def test_has_recommended_colors(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert len(result.recommended_colors) >= 10
        assert all(c.startswith("#") for c in result.recommended_colors)

    def test_has_avoid_colors(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert len(result.avoid_colors) >= 4

    def test_has_metals(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert len(result.best_metals) >= 1

    def test_has_analysis_date(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert result.analysis_date != ""

    def test_has_confidence(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert result.confidence in ("high", "medium", "low")

    def test_has_undertone(self, tmp_path):
        img = tmp_path / "photo.jpg"
        img.write_bytes(b"\xff\xd8\xff fake")
        result = analyze_colors_mock([str(img)])
        assert result.undertone in ("warm", "cool", "neutral")

    def test_empty_photos_raises(self):
        with pytest.raises(ValueError, match="At least one photo"):
            analyze_colors_mock([])


class TestLoadImageAsBase64:
    def test_loads_jpeg(self, tmp_path):
        img = tmp_path / "test.jpg"
        img.write_bytes(b"\xff\xd8\xff content here")
        data, mime = _load_image_as_base64(str(img))
        assert len(data) > 0
        assert mime == "image/jpeg"

    def test_loads_png(self, tmp_path):
        img = tmp_path / "test.png"
        img.write_bytes(b"\x89PNG content")
        data, mime = _load_image_as_base64(str(img))
        assert len(data) > 0
        assert mime == "image/png"

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            _load_image_as_base64("/no/such/file.jpg")


class TestColorAnalysisModel:
    def test_round_trip(self):
        ca = ColorAnalysis(
            season="Winter",
            sub_season="True Winter",
            undertone="cool",
            recommended_colors=["#000000", "#FFFFFF"],
            avoid_colors=["#FF8C00"],
            best_metals=["silver"],
            confidence="high",
            explanation="Test",
            analysis_date="2026-01-15",
        )
        d = ca.to_dict()
        ca2 = ColorAnalysis.from_dict(d)
        assert ca2.season == "Winter"
        assert ca2.sub_season == "True Winter"
        assert ca2.recommended_colors == ["#000000", "#FFFFFF"]

    def test_from_dict_ignores_unknown_keys(self):
        d = {"season": "Spring", "unknown_key": "value"}
        ca = ColorAnalysis.from_dict(d)
        assert ca.season == "Spring"

    def test_defaults(self):
        ca = ColorAnalysis()
        assert ca.season == ""
        assert ca.recommended_colors == []
        assert ca.best_metals == []
