"""生成戦略 generator_for_mode / DiffusionGenerator のテスト。"""
from __future__ import annotations

import io

import pytest
from PIL import Image

from app.domain.service.tryon_compositor import RingAppearance, RingPlacement
from app.domain.service.tryon_generator import (
    MODE_PHOTOREAL,
    CompositeGenerator,
    DiffusionGenerator,
    GeneratorUnavailableError,
    generator_for_mode,
)


def _white() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (120, 100), (255, 255, 255)).save(buf, format="PNG")
    return buf.getvalue()


def _placement() -> RingPlacement:
    return RingPlacement(center_x=0.5, center_y=0.5, width_ratio=0.4, angle_deg=0)


class TestGeneratorForMode:
    def test_composite_default(self):
        assert isinstance(generator_for_mode("composite"), CompositeGenerator)
        assert isinstance(generator_for_mode("unknown"), CompositeGenerator)

    def test_photoreal_is_diffusion(self):
        assert isinstance(
            generator_for_mode(MODE_PHOTOREAL, "http://diffusion"), DiffusionGenerator,
        )


class TestCompositeGenerator:
    def test_generates_png(self):
        out = CompositeGenerator().generate(_white(), _placement(), RingAppearance())
        assert Image.open(io.BytesIO(out)).format == "PNG"


class TestDiffusionGenerator:
    def test_unconfigured_raises(self):
        gen = DiffusionGenerator("")  # URL未設定
        with pytest.raises(GeneratorUnavailableError):
            gen.generate(_white(), _placement(), RingAppearance())
