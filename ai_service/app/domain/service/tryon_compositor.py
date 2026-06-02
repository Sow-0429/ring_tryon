from __future__ import annotations

import io
from dataclasses import dataclass

from PIL import Image, ImageDraw


@dataclass(frozen=True)
class RingPlacement:
    """手画像に対するリングの配置(正規化座標 + 比率)。

    center_x/center_y: 画像幅・高さに対する 0..1 の中心位置。
    width_ratio: 画像幅に対するリング幅の比率(0..1)。
    angle_deg: 指軸に合わせた回転角(度)。0 は水平バンド。
    """

    center_x: float
    center_y: float
    width_ratio: float
    angle_deg: float


@dataclass(frozen=True)
class RingAppearance:
    metal: str = "#b9975b"
    metal_dark: str = "#9c7c43"
    gem: str = "#fff6e0"


class TryOnCompositor:
    """手画像にリング(楕円バンド+ジェム)を合成して 1 枚の PNG を返す。

    将来は拡散モデル等の生成に差し替える前提の、決定的な合成ティア。
    """

    def compose(
        self,
        image_bytes: bytes,
        placement: RingPlacement,
        appearance: RingAppearance,
    ) -> bytes:
        base = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        w, h = base.size

        ring_w = max(8, int(placement.width_ratio * w))
        tile = self._render_ring_tile(ring_w, appearance)
        tile = tile.rotate(-placement.angle_deg, expand=True, resample=Image.BICUBIC)

        cx = int(placement.center_x * w)
        cy = int(placement.center_y * h)
        top_left = (cx - tile.width // 2, cy - tile.height // 2)

        base.alpha_composite(tile, dest=(max(0, top_left[0]), max(0, top_left[1])))

        out = io.BytesIO()
        base.convert("RGB").save(out, format="PNG")
        return out.getvalue()

    @staticmethod
    def _render_ring_tile(width: int, appearance: RingAppearance) -> Image.Image:
        # SVG の viewBox 120x74 を踏襲した比率で描画。
        scale = width / 120.0
        h = int(74 * scale)
        img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)

        def s(v: float) -> int:
            return int(v * scale)

        band_w = max(2, s(11))
        # バンド(楕円のアウトライン)
        d.ellipse(
            [s(8), s(14), s(112), s(70)],
            outline=appearance.metal,
            width=band_w,
        )
        # 石座 + 石 + ハイライト
        d.ellipse([s(47), s(0), s(73), s(26)], fill=appearance.metal_dark)
        d.ellipse([s(50), s(3), s(70), s(23)], fill=appearance.gem)
        d.ellipse([s(53), s(7), s(59), s(13)], fill=(255, 255, 255, 220))
        return img
