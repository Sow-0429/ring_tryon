import pytest

from app.domain.model.measurement import FingerMeasurement, RingSize, Scale


class TestScale:
    def test_px_to_mm(self):
        scale = Scale(pixels_per_mm=10.0)
        assert scale.px_to_mm(50.0) == pytest.approx(5.0)

    def test_mm_to_px(self):
        scale = Scale(pixels_per_mm=10.0)
        assert scale.mm_to_px(5.0) == pytest.approx(50.0)

    def test_invalid_scale(self):
        with pytest.raises(ValueError):
            Scale(pixels_per_mm=0.0)
        with pytest.raises(ValueError):
            Scale(pixels_per_mm=-1.0)


class TestRingSize:
    def test_jp_size_mapping(self):
        # 周囲長41mmは日本サイズ1号
        rs = RingSize(circumference_mm=41.0)
        assert rs.jp_size == 1

    def test_jp_size_closest_match(self):
        # 51.0mmは10号(50.5)か11号(51.5)のどちらかに近い
        rs = RingSize(circumference_mm=51.0)
        assert rs.jp_size in (10, 11)

    def test_jp_size_range(self):
        rs = RingSize(circumference_mm=50.5)
        low, high = rs.jp_size_range
        assert low == 9
        assert high == 11

    def test_jp_size_range_boundary(self):
        rs = RingSize(circumference_mm=41.0)  # 1号
        low, high = rs.jp_size_range
        assert low == 1  # 最小値でクランプ

    def test_us_size(self):
        rs = RingSize(circumference_mm=49.3)
        assert rs.us_size == pytest.approx(5.0, abs=0.2)

    def test_eu_size(self):
        rs = RingSize(circumference_mm=49.3)
        assert rs.eu_size == 49


class TestFingerMeasurement:
    def test_angle_deg(self):
        import math
        m = FingerMeasurement(
            finger_name="ring",
            length_mm=70.0,
            width_px=50.0,
            width_mm=15.0,
            ring_position_x=100.0,
            ring_position_y=200.0,
            finger_angle_rad=math.pi / 4,
        )
        assert m.finger_angle_deg == pytest.approx(45.0)
