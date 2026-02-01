"""Flask web application for the personal stylist."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    url_for,
)

from personal_stylist.models import (
    Category,
    ClothingItem,
    Color,
    ColorAnalysis,
    Occasion,
    Season,
    SEASON_DESCRIPTIONS,
    UserProfile,
)
from personal_stylist.recommender import OutfitRecommender
from personal_stylist.wardrobe import Wardrobe


def create_app(
    data_dir: Optional[Path] = None,
    analyzer_func=None,
) -> Flask:
    """Create the Flask application.

    Args:
        data_dir: Directory for wardrobe data persistence.
        analyzer_func: Callable for color analysis. If None, uses the real
            Claude API analyzer. Pass a mock for testing.
    """
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

    wardrobe = Wardrobe(data_dir=data_dir)

    # --- Template helpers ---
    @app.context_processor
    def inject_enums():
        return {
            "categories": [c.value for c in Category],
            "colors": [c.value for c in Color],
            "seasons": [s.value for s in Season],
            "occasions": [o.value for o in Occasion],
            "season_descriptions": SEASON_DESCRIPTIONS,
        }

    # --- Serve uploaded images ---
    @app.route("/images/<path:filename>")
    def serve_image(filename):
        images_dir = wardrobe.data_dir / "images"
        return send_from_directory(str(images_dir), filename)

    @app.route("/profile-photos/<path:filename>")
    def serve_profile_photo(filename):
        photos_dir = wardrobe.data_dir / "profile_photos"
        return send_from_directory(str(photos_dir), filename)

    # --- Pages ---
    @app.route("/")
    def index():
        items = wardrobe.items
        stats = wardrobe.stats()
        return render_template("index.html", items=items, stats=stats)

    @app.route("/add", methods=["GET", "POST"])
    def add_item():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            category = request.form.get("category", "")
            color = request.form.get("color", "")
            seasons = request.form.getlist("seasons")
            occasions = request.form.getlist("occasions")

            if not name or not category or not color:
                flash("Name, category, and color are required.", "error")
                return render_template("add.html")

            if not seasons:
                seasons = [s.value for s in Season]
            if not occasions:
                occasions = [Occasion.CASUAL.value]

            item = ClothingItem(
                name=name,
                category=category,
                color=color,
                seasons=seasons,
                occasions=occasions,
            )

            image_source = None
            uploaded = request.files.get("image")
            if uploaded and uploaded.filename:
                tmp_path = wardrobe.data_dir / "tmp_upload"
                tmp_path.mkdir(parents=True, exist_ok=True)
                tmp_file = tmp_path / uploaded.filename
                uploaded.save(str(tmp_file))
                image_source = str(tmp_file)

            try:
                wardrobe.add_item(item, image_source=image_source)
            except (FileNotFoundError, ValueError) as e:
                flash(f"Image error: {e}", "error")
                return render_template("add.html")
            finally:
                if image_source:
                    tmp = Path(image_source)
                    if tmp.exists():
                        tmp.unlink()

            flash(f"Added {item.name} to your wardrobe!", "success")
            return redirect(url_for("index"))

        return render_template("add.html")

    @app.route("/remove/<item_id>", methods=["POST"])
    def remove_item(item_id):
        removed = wardrobe.remove_item(item_id)
        if removed:
            flash(f"Removed {removed.name}.", "success")
        else:
            flash("Item not found.", "error")
        return redirect(url_for("index"))

    @app.route("/recommend", methods=["GET"])
    def recommend():
        season = request.args.get("season") or None
        occasion = request.args.get("occasion") or None
        count = int(request.args.get("count", 5))

        recommender = OutfitRecommender(wardrobe)
        outfits = recommender.recommend(
            season=season, occasion=occasion, max_results=count
        )
        return render_template(
            "recommend.html",
            outfits=outfits,
            selected_season=season,
            selected_occasion=occasion,
        )

    @app.route("/profile", methods=["GET", "POST"])
    def profile():
        if request.method == "POST":
            existing = wardrobe.profile
            name = request.form.get("name", "").strip() or "User"
            colors = request.form.getlist("preferred_colors")
            occasions = request.form.getlist("preferred_occasions")
            seasons = request.form.getlist("preferred_seasons")
            prof = UserProfile(
                name=name,
                preferred_colors=colors,
                preferred_occasions=occasions,
                preferred_seasons=seasons,
                profile_photos=existing.profile_photos if existing else [],
                color_analysis=existing.color_analysis if existing else None,
            )
            wardrobe.set_profile(prof)
            flash(f"Profile updated for {name}.", "success")
            return redirect(url_for("profile"))

        prof = wardrobe.profile
        analysis = prof.get_color_analysis() if prof else None
        photo_filenames = []
        if prof:
            for p in prof.profile_photos:
                photo_filenames.append(Path(p).name)

        return render_template(
            "profile.html",
            profile=prof,
            analysis=analysis,
            photo_filenames=photo_filenames,
        )

    @app.route("/profile/upload-photos", methods=["POST"])
    def upload_profile_photos():
        files = request.files.getlist("photos")
        if not files or not any(f.filename for f in files):
            flash("Please select at least one photo.", "error")
            return redirect(url_for("profile"))

        tmp_dir = wardrobe.data_dir / "tmp_upload"
        tmp_dir.mkdir(parents=True, exist_ok=True)
        added = 0

        for f in files:
            if not f.filename:
                continue
            tmp_file = tmp_dir / f.filename
            f.save(str(tmp_file))
            try:
                wardrobe.add_profile_photo(str(tmp_file))
                added += 1
            except (FileNotFoundError, ValueError) as e:
                flash(f"Skipped {f.filename}: {e}", "error")
            finally:
                if tmp_file.exists():
                    tmp_file.unlink()

        if added:
            flash(f"Uploaded {added} photo{'s' if added != 1 else ''}.", "success")
        return redirect(url_for("profile"))

    @app.route("/profile/remove-photo", methods=["POST"])
    def remove_profile_photo():
        photo_path = request.form.get("photo_path", "")
        if wardrobe.remove_profile_photo(photo_path):
            flash("Photo removed.", "success")
        else:
            flash("Photo not found.", "error")
        return redirect(url_for("profile"))

    @app.route("/profile/clear-photos", methods=["POST"])
    def clear_profile_photos():
        count = wardrobe.clear_profile_photos()
        if count:
            flash(f"Removed {count} photo{'s' if count != 1 else ''}.", "success")
        else:
            flash("No photos to remove.", "error")
        return redirect(url_for("profile"))

    @app.route("/profile/analyze", methods=["POST"])
    def analyze_colors_route():
        prof = wardrobe.profile
        if not prof or not prof.profile_photos:
            flash("Upload at least one photo before running color analysis.", "error")
            return redirect(url_for("profile"))

        use_mock = request.form.get("use_mock") == "1"

        try:
            if use_mock or analyzer_func:
                func = analyzer_func or _get_mock_analyzer()
                analysis = func(prof.profile_photos)
            else:
                from personal_stylist.analyzer import analyze_colors
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    flash(
                        "Set the ANTHROPIC_API_KEY environment variable to use "
                        "AI color analysis, or use the demo mode.",
                        "error",
                    )
                    return redirect(url_for("profile"))
                analysis = analyze_colors(prof.profile_photos, api_key=api_key)

            prof.set_color_analysis(analysis)
            wardrobe.set_profile(prof)
            flash("Color analysis complete!", "success")
        except Exception as e:
            flash(f"Analysis failed: {e}", "error")

        return redirect(url_for("profile"))

    return app


def _get_mock_analyzer():
    from personal_stylist.analyzer import analyze_colors_mock
    return analyze_colors_mock


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run the Personal Stylist web app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--data-dir", type=Path, default=None)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    app = create_app(data_dir=args.data_dir)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
