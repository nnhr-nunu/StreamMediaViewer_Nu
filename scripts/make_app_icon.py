"""配信画面を連想する「ぬ」アプリアイコンを PNG / ICO にする。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
MARGIN = 48
RADIUS = 236
BORDER = 30
FILL = (16, 14, 22, 255)
BORDER_COLOR = (107, 63, 160, 255)
GLYPH = (243, 233, 255, 255)
CHAR = "ぬ"
FONT_CANDIDATES = (
    Path(r"C:\Windows\Fonts\YuGothB.ttc"),
    Path(r"C:\Windows\Fonts\meiryob.ttc"),
    Path(r"C:\Windows\Fonts\BIZ-UDGothicB.ttc"),
    Path(r"C:\Windows\Fonts\NotoSansJP-VF.ttf"),
)
ICO_SIZES = ((16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256))


def _font(size: int) -> ImageFont.FreeTypeFont:
    last_error: OSError | None = None
    for path in FONT_CANDIDATES:
        if not path.is_file():
            continue
        try:
            return ImageFont.truetype(str(path), size=size, index=0)
        except OSError as exc:
            last_error = exc
    raise FileNotFoundError("日本語フォントが見つかりません") from last_error


def render_icon(size: int = SIZE) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    scale = size / SIZE
    margin = round(MARGIN * scale)
    radius = round(RADIUS * scale)
    border = max(2, round(BORDER * scale))
    box = (margin, margin, size - 1 - margin, size - 1 - margin)
    draw.rounded_rectangle(box, radius=radius, fill=FILL, outline=BORDER_COLOR, width=border)
    font = _font(max(12, round(640 * scale)))
    bbox = draw.textbbox((0, 0), CHAR, font=font)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    x = (size - width) / 2 - bbox[0]
    y = (size - height) / 2 - bbox[1] - round(18 * scale)
    draw.text((x, y), CHAR, font=font, fill=GLYPH)
    return img


def asset_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "src" / "stream_media_viewer" / "assets"


def main() -> None:
    out = asset_dir()
    out.mkdir(parents=True, exist_ok=True)
    master = render_icon()
    master.save(out / "app_icon.png", "PNG")
    master.save(out / "app_icon.ico", format="ICO", sizes=list(ICO_SIZES))
    print(out / "app_icon.png")
    print(out / "app_icon.ico")


if __name__ == "__main__":
    main()
