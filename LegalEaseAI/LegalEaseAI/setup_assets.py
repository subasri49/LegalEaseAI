"""Generates simple placeholder logos in ./Image (replace them with your own any time)."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "Image"
OUT.mkdir(exist_ok=True)


def load_font(size):
    for name in ("DejaVuSerif.ttf", "times.ttf", "georgia.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def make_logo(path, color):
    img = Image.new("RGBA", (800, 240), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx, top = 120, 40
    d.line([(cx, top + 10), (cx, 190)], fill=color, width=8)           # pillar
    d.line([(cx - 70, top + 30), (cx + 70, top + 30)], fill=color, width=8)  # beam
    for dx in (-70, 70):                                               # pans
        d.line([(cx + dx, top + 30), (cx + dx - 28, top + 100)], fill=color, width=4)
        d.line([(cx + dx, top + 30), (cx + dx + 28, top + 100)], fill=color, width=4)
        d.arc([cx + dx - 32, top + 70, cx + dx + 32, top + 130], 0, 180, fill=color, width=6)
    d.rectangle([cx - 40, 190, cx + 40, 204], fill=color)              # base
    d.text((230, 70), "LegalEase", font=load_font(96), fill=color)
    img.save(path)


make_logo(OUT / "Logo.png", (20, 33, 61, 255))
make_logo(OUT / "inverseLogo.png", (245, 245, 245, 255))
print("Logos created in", OUT)
