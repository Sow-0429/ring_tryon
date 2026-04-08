import pytest

from app.domain.model.landmark import HandLandmarks, LandmarkIndex, Point


class TestPoint:
    def test_pixel_coords(self):
        p = Point(0.5, 0.25, 0.0)
        px, py = p.pixel_coords(100, 200)
        assert px == 50.0
        assert py == 50.0

    def test_distance_to_2d(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.3, 0.4, 0.0)
        dist = p1.distance_to(p2, 100, 100)
        assert dist == pytest.approx(50.0, rel=1e-3)

    def test_distance_to_3d_no_z(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.3, 0.4, 0.0)
        dist_3d = p1.distance_to_3d(p2, 100, 100)
        dist_2d = p1.distance_to(p2, 100, 100)
        assert dist_3d == pytest.approx(dist_2d)

    def test_distance_to_3d_with_z(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.3, 0.4, 0.1)
        dist_3d = p1.distance_to_3d(p2, 100, 100)
        dist_2d = p1.distance_to(p2, 100, 100)
        assert dist_3d > dist_2d

    def test_distance_to_3d_clamped(self):
        p1 = Point(0.0, 0.0, 0.0)
        p2 = Point(0.01, 0.0, 1.0)  # 極端なz差
        dist_2d = p1.distance_to(p2, 100, 100)
        dist_3d = p1.distance_to_3d(p2, 100, 100, max_correction=1.3)
        assert dist_3d == pytest.approx(dist_2d * 1.3, rel=1e-3)

    def test_distance_to_3d_zero(self):
        p = Point(0.5, 0.5, 0.0)
        assert p.distance_to_3d(p, 100, 100) == 0.0


class TestHandLandmarks:
    def test_requires_21_points(self):
        with pytest.raises(ValueError, match="21"):
            HandLandmarks(points=[], handedness="Right", confidence=0.9)

    def test_finger_accessors(self):
        points = [Point(float(i) / 20, 0.0, 0.0) for i in range(21)]
        lm = HandLandmarks(points=points, handedness="Right", confidence=0.9)
        assert lm.finger_mcp("index") == points[LandmarkIndex.INDEX_FINGER_MCP]
        assert lm.finger_pip("middle") == points[LandmarkIndex.MIDDLE_FINGER_PIP]
        assert lm.finger_dip("ring") == points[LandmarkIndex.RING_FINGER_DIP]
        assert lm.finger_tip("pinky") == points[LandmarkIndex.PINKY_TIP]
