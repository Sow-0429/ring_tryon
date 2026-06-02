"""試着画像合成 TryOnCompositor のテスト。"""
from __future__ import annotations

import io

from PIL import Image

from app.domain.service.tryon_compositor import (
    RingAppearance,
    RingPlacement,
    TryOnCompositor,
)


def _white_image(w: int = 200, h: int = 160) -> bytes:
    img = Image.new("RGB", (w, h), (255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


class TestTryOnCompositor:
    def test_returns_png_same_size(self):
        out = TryOnCompositor().compose(
            _white_image(),
            RingPlacement(center_x=0.5, center_y=0.5, width_ratio=0.4, angle_deg=0),
            RingAppearance(),
        )
        img = Image.open(io.BytesIO(out))
        assert img.format == "PNG"
        assert img.size == (200, 160)

    def test_ring_pixels_drawn_over_white(self):
        """中央付近に白以外(リング)の画素が現れる。"""
        out = TryOnCompositor().compose(
            _white_image(),
            RingPlacement(center_x=0.5, center_y=0.5, width_ratio=0.6, angle_deg=0),
            RingAppearance(metal="#000000", metal_dark="#000000", gem="#000000"),
        )
        img = Image.open(io.BytesIO(out)).convert("RGB")
        # 全画素が白ではない(リングが描かれた)。
        colors = img.getcolors(maxcolors=100000) or []
        non_white = [c for c in colors if c[1] != (255, 255, 255)]
        assert non_white, "expected ring pixels over the white base"

    def test_angle_does_not_crash(self):
        out = TryOnCompositor().compose(
            _white_image(),
            RingPlacement(center_x=0.3, center_y=0.7, width_ratio=0.3, angle_deg=37),
            RingAppearance(),
        )
        assert Image.open(io.BytesIO(out)).size == (200, 160)
