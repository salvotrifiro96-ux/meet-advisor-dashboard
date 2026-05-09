"""Generate placeholder PNG icons for the Chrome extension.

Run once to (re)create icon16.png, icon48.png, icon128.png.
The icon is a green dot ("live") on dark background with the letter L.
Replace with real branded icons before publishing on Chrome Web Store.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BG = (16, 24, 32)        # near-black with subtle warmth
RING = (22, 163, 74)     # leone green
DOT = (34, 197, 94)      # bright green
TEXT = (240, 250, 240)


def make_icon(size: int, output_path: Path) -> None:
    img = Image.new("RGBA", (size, size), BG)
    draw = ImageDraw.Draw(img)

    # outer rounded rectangle (just background) — done above

    # ring (live indicator)
    pad = max(1, size // 16)
    ring_thickness = max(1, size // 24)
    ring_radius = size // 2 - pad
    cx = cy = size // 2

    # outer ring
    draw.ellipse(
        (cx - ring_radius, cy - ring_radius, cx + ring_radius, cy + ring_radius),
        outline=RING,
        width=ring_thickness,
    )

    # inner pulse dot
    dot_radius = size // 5
    draw.ellipse(
        (cx - dot_radius, cy - dot_radius, cx + dot_radius, cy + dot_radius),
        fill=DOT,
    )

    # letter L (try a system font, fallback to default)
    if size >= 48:
        try:
            font = ImageFont.truetype("/System/Library/Fonts/SFNS.ttf", size // 3)
        except OSError:
            font = ImageFont.load_default()

        text = "L"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            ((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1] - size // 32),
            text,
            fill=TEXT,
            font=font,
        )

    img.save(output_path, "PNG", optimize=True)


def main() -> None:
    here = Path(__file__).parent
    for size in (16, 48, 128):
        path = here / f"icon{size}.png"
        make_icon(size, path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
