from __future__ import annotations

import math

import cv2
import numpy as np

from app.domain.model.reference_object import DetectedCoin

# 円形度 4πA/P² の下限。完全円=1.0、正方形≒0.785。
CIRCULARITY_MIN = 0.80
# Hough半径から期待される面積 πr² に対し、実輪郭面積が収まるべき比の範囲。
FILL_RATIO_MIN = 0.70
FILL_RATIO_MAX = 1.40


class CoinDetector:
    """100円玉を円形基準物として検出する。

    HoughCircles候補を輪郭ベースの円形度とサイズ妥当性(充填比)で検証し、
    非円形の物体や偽検出を棄却する。
    """

    def detect(self, image: np.ndarray) -> DetectedCoin | None:
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        min_radius = max(10, int(w * 0.02))
        max_radius = int(w * 0.15)

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=50,
            param1=100,
            param2=40,
            minRadius=min_radius,
            maxRadius=max_radius,
        )

        if circles is None:
            return None

        _, binary = cv2.threshold(
            cv2.GaussianBlur(gray, (5, 5), 0),
            0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        for cx, cy, radius in sorted(circles[0], key=lambda c: -c[2]):
            if not (min_radius <= radius <= max_radius):
                continue
            circularity = self._validate(binary, cx, cy, radius)
            if circularity is None:
                continue

            confidence = min(1.0, radius / max_radius) * circularity
            return DetectedCoin(
                center_x=float(cx),
                center_y=float(cy),
                diameter_px=float(radius * 2),
                confidence=float(confidence),
            )

        return None

    def _validate(
        self, binary: np.ndarray, cx: float, cy: float, radius: float,
    ) -> float | None:
        """候補円位置の前景輪郭の円形度を返す。非円形/サイズ不一致ならNone。"""
        h, w = binary.shape[:2]
        cxi, cyi = int(round(cx)), int(round(cy))
        if not (0 <= cxi < w and 0 <= cyi < h):
            return None

        foreground = binary if binary[cyi, cxi] > 0 else cv2.bitwise_not(binary)
        contours = cv2.findContours(
            foreground, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
        )[-2]

        target = None
        for cnt in contours:
            if cv2.pointPolygonTest(cnt, (cxi, cyi), False) >= 0:
                target = cnt
                break
        if target is None:
            return None

        area = cv2.contourArea(target)
        perimeter = cv2.arcLength(target, True)
        if perimeter == 0:
            return None

        circularity = 4 * math.pi * area / (perimeter * perimeter)
        if circularity < CIRCULARITY_MIN:
            return None

        expected_area = math.pi * radius * radius
        if expected_area == 0:
            return None
        fill_ratio = area / expected_area
        if not (FILL_RATIO_MIN <= fill_ratio <= FILL_RATIO_MAX):
            return None

        return min(1.0, circularity)
