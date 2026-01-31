"""Tests for the CLI interface."""

from pathlib import Path

import pytest

from personal_stylist.cli import main
from personal_stylist.models import Category, Color, Occasion, Season
from personal_stylist.wardrobe import Wardrobe


@pytest.fixture
def data_dir(tmp_path):
    return str(tmp_path)


class TestCLI:
    def test_add_item(self, data_dir, capsys):
        main(["--data-dir", data_dir, "add", "Blue Shirt",
              "--category", "top", "--color", "blue"])
        captured = capsys.readouterr()
        assert "Added: Blue Shirt" in captured.out
        assert "blue top" in captured.out

    def test_list_empty(self, data_dir, capsys):
        main(["--data-dir", data_dir, "list"])
        captured = capsys.readouterr()
        assert "No items found" in captured.out

    def test_add_then_list(self, data_dir, capsys):
        main(["--data-dir", data_dir, "add", "Red Top",
              "--category", "top", "--color", "red"])
        main(["--data-dir", data_dir, "list"])
        captured = capsys.readouterr()
        assert "Red Top" in captured.out

    def test_add_with_seasons_and_occasions(self, data_dir, capsys):
        main(["--data-dir", data_dir, "add", "Summer Dress",
              "--category", "dress", "--color", "white",
              "--seasons", "spring", "summer",
              "--occasions", "casual", "date"])
        captured = capsys.readouterr()
        assert "Added: Summer Dress" in captured.out

    def test_stats_empty(self, data_dir, capsys):
        main(["--data-dir", data_dir, "stats"])
        captured = capsys.readouterr()
        assert "Total items: 0" in captured.out

    def test_stats_with_items(self, data_dir, capsys):
        main(["--data-dir", data_dir, "add", "Shirt",
              "--category", "top", "--color", "white"])
        main(["--data-dir", data_dir, "add", "Pants",
              "--category", "bottom", "--color", "black"])
        main(["--data-dir", data_dir, "stats"])
        captured = capsys.readouterr()
        assert "Total items: 2" in captured.out

    def test_profile_set_and_view(self, data_dir, capsys):
        main(["--data-dir", data_dir, "profile",
              "--name", "Alice", "--colors", "navy", "black"])
        capsys.readouterr()  # clear
        main(["--data-dir", data_dir, "profile"])
        captured = capsys.readouterr()
        assert "Alice" in captured.out
        assert "navy" in captured.out

    def test_profile_empty(self, data_dir, capsys):
        main(["--data-dir", data_dir, "profile"])
        captured = capsys.readouterr()
        assert "No profile set" in captured.out

    def test_recommend_empty_wardrobe(self, data_dir, capsys):
        main(["--data-dir", data_dir, "recommend"])
        captured = capsys.readouterr()
        assert "Not enough items" in captured.out

    def test_recommend_with_items(self, data_dir, capsys):
        # Add a complete outfit
        main(["--data-dir", data_dir, "add", "Shirt",
              "--category", "top", "--color", "white",
              "--occasions", "casual"])
        main(["--data-dir", data_dir, "add", "Jeans",
              "--category", "bottom", "--color", "blue",
              "--occasions", "casual"])
        main(["--data-dir", data_dir, "add", "Sneakers",
              "--category", "shoes", "--color", "white",
              "--occasions", "casual"])
        capsys.readouterr()  # clear previous output
        main(["--data-dir", data_dir, "recommend", "--occasion", "casual"])
        captured = capsys.readouterr()
        assert "Outfit" in captured.out
        assert "Score:" in captured.out

    def test_remove_item(self, data_dir, capsys):
        main(["--data-dir", data_dir, "add", "Temp Item",
              "--category", "accessory", "--color", "black"])
        captured = capsys.readouterr()
        # Extract ID from output like "Added: Temp Item [abc12345] (black accessory)"
        item_id = captured.out.split("[")[1].split("]")[0]
        main(["--data-dir", data_dir, "remove", item_id])
        captured = capsys.readouterr()
        assert "Removed: Temp Item" in captured.out

    def test_remove_nonexistent(self, data_dir, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--data-dir", data_dir, "remove", "bogus"])
        assert exc.value.code == 1

    def test_no_command_shows_help(self, data_dir, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--data-dir", data_dir])
        # argparse exits with 0 for help
        assert exc.value.code == 0

    def test_list_filter_by_category(self, data_dir, capsys):
        main(["--data-dir", data_dir, "add", "Top1",
              "--category", "top", "--color", "red"])
        main(["--data-dir", data_dir, "add", "Shoe1",
              "--category", "shoes", "--color", "black"])
        capsys.readouterr()
        main(["--data-dir", data_dir, "list", "--category", "top"])
        captured = capsys.readouterr()
        assert "Top1" in captured.out
        assert "Shoe1" not in captured.out

    def test_add_with_image(self, tmp_path, capsys):
        img = tmp_path / "shirt.jpg"
        img.write_bytes(b"\xff\xd8\xff fake jpeg")
        data_dir = str(tmp_path / "data")
        main(["--data-dir", data_dir, "add", "Photo Shirt",
              "--category", "top", "--color", "blue",
              "--image", str(img)])
        captured = capsys.readouterr()
        assert "Added: Photo Shirt" in captured.out
        assert "Image saved:" in captured.out

    def test_add_with_image_shows_in_list(self, tmp_path, capsys):
        img = tmp_path / "pants.png"
        img.write_bytes(b"\x89PNG fake png")
        data_dir = str(tmp_path / "data")
        main(["--data-dir", data_dir, "add", "Photo Pants",
              "--category", "bottom", "--color", "black",
              "--image", str(img)])
        capsys.readouterr()
        main(["--data-dir", data_dir, "list"])
        captured = capsys.readouterr()
        assert "Photo Pants" in captured.out
        assert "Image:" in captured.out

    def test_add_with_missing_image(self, data_dir, capsys):
        with pytest.raises(SystemExit) as exc:
            main(["--data-dir", data_dir, "add", "Bad Item",
                  "--category", "top", "--color", "red",
                  "--image", "/no/such/file.jpg"])
        assert exc.value.code == 1

    def test_add_with_bad_image_format(self, tmp_path, capsys):
        bad = tmp_path / "doc.txt"
        bad.write_bytes(b"not an image")
        data_dir = str(tmp_path / "data")
        with pytest.raises(SystemExit) as exc:
            main(["--data-dir", data_dir, "add", "Bad Format",
                  "--category", "top", "--color", "red",
                  "--image", str(bad)])
        assert exc.value.code == 1
