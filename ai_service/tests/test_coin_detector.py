import cv2
import numpy as np
import pytest

from app.infrastructure.coin_detector import CoinDetector


def _make_image_with_circle(
    width: int = 500,
    height: int = 500,
    circle_center: tuple[int, int] = (400, 300),
    radius: int = 30,
) -> np.ndarray:
    """白背景に灰色の円を描画したテスト画像を生成。"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    cv2.circle(img, circle_center, radius, (120, 120, 120), -1)
    return img


def _make_image_without_circle(width: int = 500, height: int = 500) -> np.ndarray:
    """円のない画像。"""
    return np.ones((height, width, 3), dtype=np.uint8) * 200


class TestCoinDetector:
    def test_detect_circle(self):
        image = _make_image_with_circle(radius=40)
        detector = CoinDetector()
        result = detector.detect(image)
        assert result is not None
        assert result.diameter_px > 0
        assert abs(result.diameter_px - 80) < 15  # 直径80px前後

    def test_detect_returns_center(self):
        image = _make_image_with_circle(circle_center=(250, 250), radius=35)
        detector = CoinDetector()
        result = detector.detect(image)
        assert result is not None
        assert abs(result.center_x - 250) < 20
        assert abs(result.center_y - 250) < 20

    def test_detect_no_circle(self):
        image = _make_image_without_circle()
        detector = CoinDetector()
        result = detector.detect(image)
        assert result is None

    def test_detect_confidence(self):
        image = _make_image_with_circle(radius=40)
        detector = CoinDetector()
        result = detector.detect(image)
        assert result is not None
        assert 0.0 <= result.confidence <= 1.0
