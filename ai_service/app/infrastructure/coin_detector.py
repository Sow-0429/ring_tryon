from __future__ import annotations

import cv2
import numpy as np

from app.domain.model.reference_object import DetectedCoin


class CoinDetector:
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

        circles = circles[0]
        best = max(circles, key=lambda c: c[2])
        cx, cy, radius = best

        confidence = min(1.0, radius / max_radius)

        return DetectedCoin(
            center_x=float(cx),
            center_y=float(cy),
            diameter_px=float(radius * 2),
            confidence=confidence,
        )
