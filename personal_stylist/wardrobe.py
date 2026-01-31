"""Wardrobe management - add, remove, list, and persist clothing items."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Optional

from personal_stylist.models import ClothingItem, UserProfile, Category


DEFAULT_DATA_DIR = Path.home() / ".personal_stylist"
WARDROBE_FILE = "wardrobe.json"
PROFILE_FILE = "profile.json"
IMAGES_DIR = "images"

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}


class Wardrobe:
    """Manages a collection of clothing items with JSON persistence."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._items: list[ClothingItem] = []
        self._profile: Optional[UserProfile] = None
        self._load()

    # -- Persistence --

    def _wardrobe_path(self) -> Path:
        return self.data_dir / WARDROBE_FILE

    def _profile_path(self) -> Path:
        return self.data_dir / PROFILE_FILE

    def _load(self) -> None:
        wp = self._wardrobe_path()
        if wp.exists():
            with open(wp, "r") as f:
                data = json.load(f)
            self._items = [ClothingItem.from_dict(d) for d in data]

        pp = self._profile_path()
        if pp.exists():
            with open(pp, "r") as f:
                data = json.load(f)
            self._profile = UserProfile.from_dict(data)

    def save(self) -> None:
        with open(self._wardrobe_path(), "w") as f:
            json.dump([item.to_dict() for item in self._items], f, indent=2)

        if self._profile:
            with open(self._profile_path(), "w") as f:
                json.dump(self._profile.to_dict(), f, indent=2)

    # -- Profile --

    @property
    def profile(self) -> Optional[UserProfile]:
        return self._profile

    def set_profile(self, profile: UserProfile) -> None:
        self._profile = profile
        self.save()

    # -- Item management --

    @property
    def items(self) -> list[ClothingItem]:
        return list(self._items)

    def _images_path(self) -> Path:
        return self.data_dir / IMAGES_DIR

    def add_item(self, item: ClothingItem, image_source: Optional[str] = None) -> ClothingItem:
        if image_source:
            item.image_path = self._store_image(item.id, image_source)
        self._items.append(item)
        self.save()
        return item

    def _store_image(self, item_id: str, source_path: str) -> str:
        """Copy an image file into the wardrobe images directory.

        Returns the path to the stored copy.
        """
        src = Path(source_path)
        if not src.exists():
            raise FileNotFoundError(f"Image not found: {source_path}")
        ext = src.suffix.lower()
        if ext not in SUPPORTED_IMAGE_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_IMAGE_EXTENSIONS))}"
            )
        images_dir = self._images_path()
        images_dir.mkdir(parents=True, exist_ok=True)
        dest = images_dir / f"{item_id}{ext}"
        shutil.copy2(str(src), str(dest))
        return str(dest)

    def remove_item(self, item_id: str) -> Optional[ClothingItem]:
        for i, item in enumerate(self._items):
            if item.id == item_id:
                removed = self._items.pop(i)
                if removed.image_path:
                    img = Path(removed.image_path)
                    if img.exists():
                        img.unlink()
                self.save()
                return removed
        return None

    def get_item(self, item_id: str) -> Optional[ClothingItem]:
        for item in self._items:
            if item.id == item_id:
                return item
        return None

    def find_items(
        self,
        category: Optional[str] = None,
        color: Optional[str] = None,
        season: Optional[str] = None,
        occasion: Optional[str] = None,
    ) -> list[ClothingItem]:
        """Filter wardrobe items by criteria."""
        results = self._items
        if category:
            results = [i for i in results if i.category == category]
        if color:
            results = [i for i in results if i.color == color]
        if season:
            results = [i for i in results if i.matches_season(season)]
        if occasion:
            results = [i for i in results if i.matches_occasion(occasion)]
        return results

    def list_by_category(self) -> dict[str, list[ClothingItem]]:
        """Group wardrobe items by category."""
        grouped: dict[str, list[ClothingItem]] = {}
        for item in self._items:
            grouped.setdefault(item.category, []).append(item)
        return grouped

    def stats(self) -> dict[str, int]:
        """Return wardrobe statistics."""
        by_cat = self.list_by_category()
        result = {"total": len(self._items)}
        for cat in Category:
            result[cat.value] = len(by_cat.get(cat.value, []))
        return result
