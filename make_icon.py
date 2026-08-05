#!/usr/bin/env python3
"""Turn generated glyphs into category icons that match the existing set.

    python3 make_icon.py <source.png> <category-slug>       # one icon
    python3 make_icon.py --sheet <sheet.png> [cols] [rows]  # a whole grid

Midjourney gives you a textured square with the glyph at whatever size and
colour it felt like. The icons here are 120x120, flat #F2EFE9, one deep-olive
glyph filling ~55% of the canvas. This does that conversion: crop to the ink,
rescale to the house proportion, recolour to the exact palette, and drop the
paper texture out of the background.

Sheet mode slices a grid left-to-right, top-to-bottom and assigns SHEET_ORDER
to the cells — which is the whole point of generating them in one prompt, so
stroke weight and character stay identical across the set.

Prints a 16px ASCII preview, because 16px is the size that actually decides
whether an icon works — that's how it renders in the nav.
"""
import os
import sys

from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "assets", "icons")

SIZE = 120
FILL = 0.55            # glyph's long edge as a share of the canvas
PAPER = (242, 239, 233)  # #F2EFE9
INK = (52, 83, 31)       # #34531F
INK_AT = 165           # luminance at or below this is fully ink
INK_HARD = 140         # strict cut used for the crop box (ignores paper texture)
PAPER_AT = 225         # luminance at or above this is fully background


# Cell order for --sheet, left to right then top to bottom.
SHEET_ORDER = [
    "software-tools", "ai-tools", "business", "learning",
    "entertainment", "books-reading", "money-finance", "earn",
    "reviews", "leisure", "data-apis", "deals",
]


def conform(src, label=""):
    """Crop to the ink, rescale to the house proportion, recolour. -> RGB 120px"""
    src = src.convert("L")

    # Luminance -> alpha. Everything between the two thresholds ramps, which
    # keeps the antialiasing on curves instead of hard-edging them.
    span = max(1, PAPER_AT - INK_AT)
    alpha = src.point(lambda v: 255 if v <= INK_AT else
                      (0 if v >= PAPER_AT else int(255 * (PAPER_AT - v) / span)))

    # Crop from a STRICT mask, not the soft one. Generated art carries paper
    # texture that dips just under the soft threshold, and a few stray specks
    # in the corners blow the bbox out to the whole cell — which silently
    # shrinks the glyph instead of failing. Median filter kills the specks;
    # the hard cut ignores anything that isn't solid ink.
    hard = src.point(lambda v: 255 if v <= INK_HARD else 0).filter(
        ImageFilter.MedianFilter(3))
    box = hard.getbbox()
    if not box:
        return None
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
    canvas.info["_glyph"] = alpha.size
    return canvas


def save(canvas, slug):
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, f"{slug}.png")
    canvas.save(dest, optimize=True)
    gw, gh = canvas.info.get("_glyph", (0, 0))
    ink = sum(1 for p in canvas.get_flattened_data() if sum(p) < 450)
    print(f"  {slug:16} glyph {gw:3}x{gh:3} · fill {max(gw, gh)/SIZE:.0%} "
          f"· ink {ink*100//(SIZE*SIZE):2}%")
    return dest


def build(src_path, slug):
    canvas = conform(Image.open(src_path))
    if canvas is None:
        sys.exit(f"no glyph found in {src_path} — is it very light, or inverted?")
    print(f"wrote {OUT_DIR}")
    save(canvas, slug)
    return canvas


def build_sheet(src_path, cols=4, rows=3):
    sheet = Image.open(src_path)
    W, H = sheet.size
    cw, ch = W // cols, H // rows
    if len(SHEET_ORDER) < cols * rows:
        sys.exit(f"SHEET_ORDER has {len(SHEET_ORDER)} names for {cols*rows} cells")
    print(f"slicing {W}x{H} into {cols}x{rows} cells of {cw}x{ch}\n")
    done, blank = [], []
    for i in range(cols * rows):
        x, y = (i % cols) * cw, (i // cols) * ch
        canvas = conform(sheet.crop((x, y, x + cw, y + ch)))
        slug = SHEET_ORDER[i]
        if canvas is None:
            blank.append(slug)
            continue
        save(canvas, slug)
        done.append((slug, canvas))
    if blank:
        print(f"\n  EMPTY CELLS (re-roll these): {', '.join(blank)}")
    print(f"\n{len(done)}/{cols*rows} cells written")
    return done


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
    a = sys.argv[1:]
    if a and a[0] == "--sheet":
        if len(a) < 2:
            sys.exit(__doc__)
        cols = int(a[2]) if len(a) > 2 else 4
        rows = int(a[3]) if len(a) > 3 else 3
        for slug, canvas in build_sheet(a[1], cols, rows):
            print(f"\n=== {slug}")
            preview(canvas)
    elif len(a) == 2:
        preview(build(a[0], a[1]))
    else:
        sys.exit(__doc__)
