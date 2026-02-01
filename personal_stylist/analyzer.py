"""Color analysis using Claude API with vision capabilities.

Analyzes user profile photos to determine seasonal color type,
recommended color palette, and styling advice.
"""

from __future__ import annotations

import base64
import json
import mimetypes
from datetime import date
from pathlib import Path
from typing import Optional

from personal_stylist.models import ColorAnalysis


ANALYSIS_PROMPT = """\
Analyze these {count} photos of the user to determine their personal seasonal \
color type for fashion and styling purposes.

Consider carefully:
- Skin undertone and depth (warm, cool, or neutral)
- Natural hair color and tone
- Eye color
- Overall contrast level between skin, hair, and eyes
- How different color temperatures would appear against their skin

Check for consistency across all provided photos before making your assessment.

Provide your analysis as a JSON object with exactly these fields:
{{
  "season": "one of: Spring, Summer, Autumn, Winter",
  "sub_season": "specific subtype, e.g. Soft Summer, True Winter, Deep Autumn, Bright Spring, etc.",
  "undertone": "warm, cool, or neutral",
  "recommended_colors": ["12-16 hex color codes that would flatter this person, e.g. #8B4513"],
  "avoid_colors": ["6-8 hex color codes that would clash with their coloring"],
  "best_metals": ["list from: gold, silver, rose gold"],
  "confidence": "high, medium, or low",
  "explanation": "2-3 sentence explanation of why this seasonal type fits, referencing specific features observed"
}}

Return ONLY the JSON object, no other text.\
"""


def _load_image_as_base64(path: str) -> tuple[str, str]:
    """Load an image file and return (base64_data, media_type)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Photo not found: {path}")

    mime, _ = mimetypes.guess_type(str(p))
    if not mime or not mime.startswith("image/"):
        mime = "image/jpeg"

    with open(p, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("ascii")
    return data, mime


def _preprocess_image(path: str, max_size: int = 1024) -> str:
    """Resize image if needed. Returns path to the (possibly resized) file.

    Uses PIL if available, otherwise returns the original path.
    """
    try:
        from PIL import Image
    except ImportError:
        return path

    img = Image.open(path)
    if max(img.size) <= max_size:
        return path

    img.thumbnail((max_size, max_size), Image.LANCZOS)
    out_path = Path(path).with_suffix(".resized.jpg")
    img = img.convert("RGB")
    img.save(str(out_path), "JPEG", quality=85)
    return str(out_path)


def analyze_colors(
    photo_paths: list[str],
    api_key: Optional[str] = None,
) -> ColorAnalysis:
    """Analyze user photos via Claude API to determine seasonal color type.

    Args:
        photo_paths: List of 1-10 file paths to user profile photos.
        api_key: Anthropic API key. If None, reads from ANTHROPIC_API_KEY env var.

    Returns:
        ColorAnalysis with seasonal type, palette, and recommendations.

    Raises:
        ValueError: If no photos provided or too many photos.
        RuntimeError: If API call fails or response can't be parsed.
    """
    if not photo_paths:
        raise ValueError("At least one photo is required for color analysis.")
    if len(photo_paths) > 10:
        raise ValueError("Maximum 10 photos allowed for analysis.")

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    content: list[dict] = []
    resized_paths: list[str] = []

    for path in photo_paths:
        processed = _preprocess_image(path)
        resized_paths.append(processed)
        b64_data, media_type = _load_image_as_base64(processed)
        content.append({
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64_data,
            },
        })

    content.append({
        "type": "text",
        "text": ANALYSIS_PROMPT.format(count=len(photo_paths)),
    })

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": content}],
        )
    except Exception as e:
        raise RuntimeError(f"Claude API call failed: {e}") from e
    finally:
        for rp in resized_paths:
            if rp != photo_paths[resized_paths.index(rp)]:
                p = Path(rp)
                if p.exists():
                    p.unlink()

    raw_text = response.content[0].text.strip()

    # Extract JSON from response (handle potential markdown code blocks)
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        json_lines = []
        inside = False
        for line in lines:
            if line.startswith("```") and not inside:
                inside = True
                continue
            elif line.startswith("```") and inside:
                break
            elif inside:
                json_lines.append(line)
        raw_text = "\n".join(json_lines)

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Failed to parse Claude response as JSON: {e}\nRaw: {raw_text[:500]}"
        ) from e

    analysis = ColorAnalysis.from_dict(data)
    analysis.analysis_date = date.today().isoformat()
    return analysis


def analyze_colors_mock(photo_paths: list[str]) -> ColorAnalysis:
    """Mock analysis for testing/demo without API access.

    Returns a plausible color analysis based on the number of photos provided.
    """
    if not photo_paths:
        raise ValueError("At least one photo is required for color analysis.")

    return ColorAnalysis(
        season="Autumn",
        sub_season="Soft Autumn",
        undertone="warm",
        recommended_colors=[
            "#8B6914", "#CD853F", "#D2691E", "#A0522D", "#BC8F8F",
            "#DAA520", "#6B8E23", "#556B2F", "#8FBC8F", "#B8860B",
            "#C19A6B", "#E8DCCA", "#F5DEB3", "#FAEBD7", "#D2B48C",
            "#CC7722",
        ],
        avoid_colors=[
            "#FF00FF", "#00FFFF", "#FF1493", "#7FFF00",
            "#FF69B4", "#00CED1",
        ],
        best_metals=["gold", "rose gold"],
        confidence="medium",
        explanation=(
            "Based on the provided photos, you appear to have warm undertones "
            "with medium contrast. Earth tones and warm, muted colors will "
            "complement your natural coloring beautifully."
        ),
        analysis_date=date.today().isoformat(),
    )
