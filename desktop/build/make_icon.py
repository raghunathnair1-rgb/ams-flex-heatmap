"""Generates the desktop app icon (a simple paper-plane mark) as PNG/ICO/ICNS.
Run once locally; outputs are committed since not every contributor has
iconutil (macOS-only) to regenerate the .icns.
"""
from PIL import Image, ImageDraw
import subprocess
import sys
from pathlib import Path

OUT = Path(__file__).parent
SIZE = 1024
BG = (47, 104, 201)  # matches --accent in the web app
FG = (255, 255, 255)


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    r = size * 0.22
    d.rounded_rectangle([0, 0, size, size], radius=r, fill=BG)

    # Simple paper-plane silhouette, centered.
    cx, cy = size / 2, size / 2
    s = size * 0.32
    points = [
        (cx - s, cy + s * 0.55),
        (cx + s * 1.15, cy - s * 0.05),
        (cx - s * 0.25, cy + s * 0.15),
        (cx - s * 0.05, cy + s * 0.95),
        (cx - s * 0.35, cy + s * 0.35),
    ]
    d.polygon(points, fill=FG)
    return img


def main():
    base = draw_icon(SIZE)
    base.save(OUT / "icon.png")

    # .ico with multiple sizes
    ico_sizes = [16, 24, 32, 48, 64, 128, 256]
    imgs = [draw_icon(s) for s in ico_sizes]
    imgs[-1].save(OUT / "icon.ico", sizes=[(s, s) for s in ico_sizes])

    # .icns (macOS only, via iconutil)
    if sys.platform == "darwin":
        iconset = OUT / "icon.iconset"
        iconset.mkdir(exist_ok=True)
        mac_sizes = {
            "icon_16x16.png": 16, "icon_16x16@2x.png": 32,
            "icon_32x32.png": 32, "icon_32x32@2x.png": 64,
            "icon_128x128.png": 128, "icon_128x128@2x.png": 256,
            "icon_256x256.png": 256, "icon_256x256@2x.png": 512,
            "icon_512x512.png": 512, "icon_512x512@2x.png": 1024,
        }
        for name, s in mac_sizes.items():
            draw_icon(s).save(iconset / name)
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(OUT / "icon.icns")], check=True)
        for f in iconset.glob("*.png"):
            f.unlink()
        iconset.rmdir()
        print("Wrote icon.png, icon.ico, icon.icns")
    else:
        print("Wrote icon.png, icon.ico (icon.icns needs macOS/iconutil)")


if __name__ == "__main__":
    main()
