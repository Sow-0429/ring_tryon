from __future__ import annotations

import cv2
import numpy as np

from app.domain.model.landmark import HandLandmarks


class HandSegmenter:
    """手シルエットの二値マスクを抽出する。

    Otsuで領域分割し、ランドマークが指す側を前景として選ぶため、
    背景や照明の絶対値・極性(手が明るい/暗い)に依存しない。
    ランドマークを最も多く含む連結成分のみを採用し、背景ノイズを除く。
    """

    def segment(self, image: np.ndarray, landmarks: HandLandmarks) -> np.ndarray:
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        points_px = [lm.pixel_coords(w, h) for lm in landmarks.points]

        white_votes = sum(
            1
            for (px, py) in points_px
            if self._in_bounds(px, py, w, h) and binary[int(py), int(px)] > 0
        )
        foreground = binary if white_votes * 2 >= len(points_px) else cv2.bitwise_not(binary)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)
        foreground = cv2.morphologyEx(foreground, cv2.MORPH_OPEN, kernel)

        num_labels, labels = cv2.connectedComponents(foreground)
        if num_labels <= 1:
            return foreground.astype(bool)

        label_votes: dict[int, int] = {}
        for (px, py) in points_px:
            if not self._in_bounds(px, py, w, h):
                continue
            label = int(labels[int(py), int(px)])
            if label != 0:
                label_votes[label] = label_votes.get(label, 0) + 1

        if not label_votes:
            return foreground.astype(bool)

        best_label = max(label_votes, key=label_votes.get)
        return labels == best_label

    @staticmethod
    def _in_bounds(px: float, py: float, w: int, h: int) -> bool:
        return 0 <= int(px) < w and 0 <= int(py) < h
