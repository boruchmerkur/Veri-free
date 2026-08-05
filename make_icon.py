#!/usr/bin/env python3
"""Turn a generated glyph into a category icon that matches the existing set.

    python3 make_icon.py <source.png> <category-slug>

Midjourney gives you a 1024px textured square with the glyph at whatever size
and colour it felt like. The existing icons are 120x120, flat #F2EFE9, one
deep-olive glyph filling ~55% of the canvas. This does that conversion:
crop to the ink, rescale to the house proportion, recolour to the exact
palette, and drop the paper texture out of the background.

Prints a 16px ASCII preview at the end, because 16px is the size that
actually decides whether an icon works — that's how it renders in the nav.
"""
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "assets", "icons")

SIZE = 120
FILL = 0.55            # glyph's long edge as a share of the canvas
PAPER = (242, 239, 233)  # #F2EFE9
INK = (52, 83, 31)       # #34531F
INK_AT = 165           # luminance at or below this is fully ink
PAPER_AT = 225         # luminance at or above this is fully background


def build(src_path, slug):
    src = Image.open(src_path).convert("L")

    # Luminance -> alpha. Everything between the two thresholds ramps, which
    # keeps the antialiasing on curves instead of hard-edging them.
    span = max(1, PAPER_AT - INK_AT)
    alpha = src.point(lambda v: 255 if v <= INK_AT else
                      (0 if v >= PAPER_AT else int(255 * (PAPER_AT - v) / span)))

    box = alpha.getbbox()
    if not box:
        sys.exit(f"no glyph found in {src_path} — is it very light, or inverted?")
    alpha = alpha.crop(box)

    # Rescale so the long edge hits the house proportion.
    w, h = alpha.size
    scale = (SIZE * FILL) / max(w, h)
    alpha = alpha.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                         Image.LANCZOS)

    canvas = Image.new("RGB", (SIZE, SIZE), PAPER)
    glyph = Image.new("RGB", alpha.size, INK)
    canvas.paste(glyph, ((SIZE - alpha.size[0]) // 2,
                         (SIZE - alpha.size[1]) // 2), alpha)

    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, f"{slug}.png")
    canvas.save(dest, optimize=True)

    ink_px = sum(1 for p in canvas.get_flattened_data() if sum(p) < 450)
    print(f"wrote {dest}")
    print(f"  glyph {alpha.size[0]}x{alpha.size[1]} of {SIZE} "
          f"(fill {max(alpha.size)/SIZE:.0%}) · ink {ink_px*100//(SIZE*SIZE)}%")
    return canvas


def preview(canvas):
    """The 16px legibility test, as ASCII — dense blocks are ink."""
    small = canvas.convert("L").resize((16, 16), Image.LANCZOS)
    ramp = "@%#*+=-:. "
    print("\n  16px preview (what the nav actually renders):")
    px = small.load()
    for y in range(16):
        print("   " + "".join(ramp[min(9, px[x, y] * 10 // 256)] * 2
                              for x in range(16)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    preview(build(sys.argv[1], sys.argv[2]))
