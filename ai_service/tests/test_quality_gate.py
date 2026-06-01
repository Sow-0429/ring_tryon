"""撮影品質ゲート QualityGate のテスト。

手の平坦さ(z分散)・指の直線性・ブレ(Laplacian分散)・露出を検査し、
不合格は実用的なメッセージ付きで返すことを検証する。
TDD red phase: app.domain.model.quality / app.domain.service.quality_gate は未実装の想定。
"""
from __future__ import annotations

import cv2
import numpy as np

from app.domain.model.landmark import Point
from app.domain.service.quality_gate import QualityGate
from tests.conftest import make_hand_landmarks


def _sharp_well_exposed_image(w: int = 400, h: int = 400) -> np.ndarray:
    """高コントラストのチェッカー模様(鮮鋭・中庸な露出)。"""
    rng = np.random.default_rng(42)
    img = rng.integers(60, 200, size=(h, w, 3), dtype=np.uint8)
    return img


def _blurry_image() -> np.ndarray:
    img = _sharp_well_exposed_image()
    return cv2.GaussianBlur(img, (31, 31), 0)


def _dark_image(w: int = 400, h: int = 400) -> np.ndarray:
    return np.full((h, w, 3), 8, dtype=np.uint8)


def _bright_image(w: int = 400, h: int = 400) -> np.ndarray:
    return np.full((h, w, 3), 252, dtype=np.uint8)


def _curled_finger_landmarks():
    """人差し指のPIP/DIPがMCP→TIP軸から大きく外れた(曲がった)ランドマーク。"""
    points = make_hand_landmarks().points.copy()
    # INDEX: MCP=5, PIP=6, DIP=7, TIP=8
    points[5] = Point(0.40, 0.55, 0.0)
    points[6] = Point(0.50, 0.45, 0.0)  # 軸から横に大きく逸脱
    points[7] = Point(0.48, 0.35, 0.0)
    points[8] = Point(0.40, 0.25, 0.0)
    return make_hand_landmarks(points=points)


def _tilted_hand_landmarks():
    """zが指先に向かって大きく変化する(平らでない)ランドマーク。"""
    base = make_hand_landmarks().points
    points = [Point(p.x, p.y, p.y * 0.6) for p in base]  # yに比例した深さ
    return make_hand_landmarks(points=points)


def _check(assessment, name):
    return next(c for c in assessment.checks if c.name == name)


class TestQualityGate:
    def test_good_input_passes(self):
        image = _sharp_well_exposed_image()
        landmarks = make_hand_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        assert result.is_acceptable
        assert result.failure_messages == []

    def test_blurry_image_fails_sharpness(self):
        image = _blurry_image()
        landmarks = make_hand_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        assert not result.is_acceptable
        assert not _check(result, "sharpness").passed
        assert result.failure_messages  # 非空の実用メッセージ

    def test_dark_image_fails_exposure(self):
        image = _dark_image()
        landmarks = make_hand_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        assert not result.is_acceptable
        assert not _check(result, "exposure").passed

    def test_bright_image_fails_exposure(self):
        image = _bright_image()
        landmarks = make_hand_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        assert not _check(result, "exposure").passed

    def test_tilted_hand_fails_flatness(self):
        image = _sharp_well_exposed_image()
        landmarks = _tilted_hand_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        assert not _check(result, "flatness").passed

    def test_curled_finger_fails_straightness(self):
        image = _sharp_well_exposed_image()
        landmarks = _curled_finger_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        assert not _check(result, "straightness").passed

    def test_failure_messages_are_practical(self):
        image = _dark_image()
        landmarks = make_hand_landmarks()

        result = QualityGate().evaluate(image, landmarks)

        # 不合格メッセージは空でなく、検査数と整合する
        assert len(result.failure_messages) >= 1
        assert all(isinstance(m, str) and m for m in result.failure_messages)
