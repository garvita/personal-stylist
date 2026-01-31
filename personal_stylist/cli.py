"""Command-line interface for the personal stylist application."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stylist",
        description="Personal Stylist - manage your wardrobe and get outfit recommendations",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Directory for wardrobe data (default: ~/.personal_stylist)",
    )
    sub = parser.add_subparsers(dest="command")

    # -- add --
    add_p = sub.add_parser("add", help="Add a clothing item to your wardrobe")
    add_p.add_argument("name", help="Name of the item (e.g. 'Blue Oxford Shirt')")
    add_p.add_argument(
        "--category", "-c",
        required=True,
        choices=[c.value for c in Category],
        help="Clothing category",
    )
    add_p.add_argument(
        "--color", "-C",
        required=True,
        choices=[c.value for c in Color],
        help="Primary color",
    )
    add_p.add_argument(
        "--seasons", "-s",
        nargs="+",
        choices=[s.value for s in Season],
        default=[s.value for s in Season],
        help="Suitable seasons (default: all)",
    )
    add_p.add_argument(
        "--occasions", "-o",
        nargs="+",
        choices=[o.value for o in Occasion],
        default=[Occasion.CASUAL.value],
        help="Suitable occasions (default: casual)",
    )
    add_p.add_argument(
        "--image", "-i",
        type=str,
        default=None,
        help="Path to a photo of the item (jpg, png, gif, webp, bmp)",
    )

    # -- remove --
    rm_p = sub.add_parser("remove", help="Remove a clothing item by ID")
    rm_p.add_argument("id", help="Item ID to remove")

    # -- list --
    list_p = sub.add_parser("list", help="List wardrobe items")
    list_p.add_argument(
        "--category",
        choices=[c.value for c in Category],
        help="Filter by category",
    )
    list_p.add_argument(
        "--color",
        choices=[c.value for c in Color],
        help="Filter by color",
    )
    list_p.add_argument(
        "--season",
        choices=[s.value for s in Season],
        help="Filter by season",
    )
    list_p.add_argument(
        "--occasion",
        choices=[o.value for o in Occasion],
        help="Filter by occasion",
    )

    # -- stats --
    sub.add_parser("stats", help="Show wardrobe statistics")

    # -- recommend --
    rec_p = sub.add_parser("recommend", help="Get outfit recommendations")
    rec_p.add_argument(
        "--season",
        choices=[s.value for s in Season],
        help="Season to dress for",
    )
    rec_p.add_argument(
        "--occasion",
        choices=[o.value for o in Occasion],
        help="Occasion to dress for",
    )
    rec_p.add_argument(
        "--count", "-n",
        type=int,
        default=5,
        help="Number of recommendations (default: 5)",
    )

    # -- profile --
    prof_p = sub.add_parser("profile", help="Set or view your style profile")
    prof_p.add_argument("--name", help="Your name")
    prof_p.add_argument(
        "--colors",
        nargs="+",
        choices=[c.value for c in Color],
        help="Preferred colors",
    )
    prof_p.add_argument(
        "--occasions",
        nargs="+",
        choices=[o.value for o in Occasion],
        help="Preferred occasions",
    )
    prof_p.add_argument(
        "--seasons",
        nargs="+",
        choices=[s.value for s in Season],
        help="Preferred seasons",
    )

    return parser


def cmd_add(wardrobe: Wardrobe, args: argparse.Namespace) -> None:
    item = ClothingItem(
        name=args.name,
        category=args.category,
        color=args.color,
        seasons=args.seasons,
        occasions=args.occasions,
    )
    try:
        wardrobe.add_item(item, image_source=args.image)
    except (FileNotFoundError, ValueError) as e:
        print(f"Image error: {e}", file=sys.stderr)
        sys.exit(1)
    msg = f"Added: {item.name} [{item.id}] ({item.color} {item.category})"
    if item.image_path:
        msg += f"\n  Image saved: {item.image_path}"
    print(msg)


def cmd_remove(wardrobe: Wardrobe, args: argparse.Namespace) -> None:
    removed = wardrobe.remove_item(args.id)
    if removed:
        print(f"Removed: {removed.name} [{removed.id}]")
    else:
        print(f"Item not found: {args.id}", file=sys.stderr)
        sys.exit(1)


def cmd_list(wardrobe: Wardrobe, args: argparse.Namespace) -> None:
    items = wardrobe.find_items(
        category=args.category,
        color=args.color,
        season=args.season,
        occasion=args.occasion,
    )
    if not items:
        print("No items found.")
        return
    for item in items:
        seasons = ", ".join(item.seasons)
        occasions = ", ".join(item.occasions)
        line = (f"  [{item.id}] {item.name} - {item.color} {item.category} "
                f"(seasons: {seasons} | occasions: {occasions})")
        if item.image_path:
            line += f"\n           Image: {item.image_path}"
        print(line)


def cmd_stats(wardrobe: Wardrobe, _args: argparse.Namespace) -> None:
    st = wardrobe.stats()
    print(f"Total items: {st['total']}")
    for cat in Category:
        count = st.get(cat.value, 0)
        if count:
            print(f"  {cat.value}: {count}")


def cmd_recommend(wardrobe: Wardrobe, args: argparse.Namespace) -> None:
    recommender = OutfitRecommender(wardrobe)
    outfits = recommender.recommend(
        season=args.season,
        occasion=args.occasion,
        max_results=args.count,
    )
    if not outfits:
        print("Not enough items to generate outfit recommendations.")
        print("Add more items with: stylist add <name> --category <cat> --color <color>")
        return

    print(f"Top {len(outfits)} outfit recommendations:")
    for i, outfit in enumerate(outfits, 1):
        print(f"\nOutfit {i}:")
        print(outfit.describe())


def cmd_profile(wardrobe: Wardrobe, args: argparse.Namespace) -> None:
    # If no flags provided, show current profile
    if not any([args.name, args.colors, args.occasions, args.seasons]):
        profile = wardrobe.profile
        if profile:
            print(f"Name: {profile.name}")
            if profile.preferred_colors:
                print(f"Preferred colors: {', '.join(profile.preferred_colors)}")
            if profile.preferred_occasions:
                print(f"Preferred occasions: {', '.join(profile.preferred_occasions)}")
            if profile.preferred_seasons:
                print(f"Preferred seasons: {', '.join(profile.preferred_seasons)}")
        else:
            print("No profile set. Use: stylist profile --name <name> [--colors ...] [--occasions ...]")
        return

    existing = wardrobe.profile
    profile = UserProfile(
        name=args.name or (existing.name if existing else "User"),
        preferred_colors=args.colors or (existing.preferred_colors if existing else []),
        preferred_occasions=args.occasions or (existing.preferred_occasions if existing else []),
        preferred_seasons=args.seasons or (existing.preferred_seasons if existing else []),
    )
    wardrobe.set_profile(profile)
    print(f"Profile updated for {profile.name}.")


COMMANDS = {
    "add": cmd_add,
    "remove": cmd_remove,
    "list": cmd_list,
    "stats": cmd_stats,
    "recommend": cmd_recommend,
    "profile": cmd_profile,
}


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    wardrobe = Wardrobe(data_dir=args.data_dir)
    handler = COMMANDS.get(args.command)
    if handler:
        handler(wardrobe, args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
