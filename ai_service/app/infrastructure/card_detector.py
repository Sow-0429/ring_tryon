from __future__ import annotations

import cv2
import numpy as np

from app.domain.model.reference_object import CARD_ID1_ASPECT_RATIO, DetectedCard

# 検出カードのアスペクト比がID-1規格からこの幅を超えて外れたら棄却する
ASPECT_TOLERANCE = 0.3
# カード矩形とみなす面積(画像面積比)の下限・上限
MIN_AREA_RATIO = 0.01
MAX_AREA_RATIO = 0.95


class CardDetector:
    """ID-1カード(85.60×53.98mm)を矩形として検出する。

    Otsuしきい値で領域分割し、全輪郭(RETR_LIST)から minAreaRect で矩形を
    フィットする。アスペクト比がID-1規格に近く面積が妥当なものを採用する。
    minAreaRect を使うことでエッジ膨張や多角形近似誤差による寸法インフレを避ける。
    """

    def detect(self, image: np.ndarray) -> DetectedCard | None:
        h, w = image.shape[:2]
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        _, binary = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU,
        )

        contours = cv2.findContours(
            binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE,
        )[-2]

        image_area = float(w * h)
        min_area = image_area * MIN_AREA_RATIO
        max_area = image_area * MAX_AREA_RATIO

        best: DetectedCard | None = None
        best_area = 0.0

        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            (rw, rh) = rect[1]
            rect_area = rw * rh
            if rect_area < min_area or rect_area > max_area:
                continue

            long_edge = max(rw, rh)
            short_edge = min(rw, rh)
            if short_edge == 0:
                continue
            aspect = long_edge / short_edge
            aspect_diff = abs(aspect - CARD_ID1_ASPECT_RATIO)
            if aspect_diff > ASPECT_TOLERANCE:
                continue

            if rect_area > best_area:
                corners = self._order_corners(cv2.boxPoints(rect))
                confidence = min(
                    1.0, max(0.0, 1.0 - aspect_diff / CARD_ID1_ASPECT_RATIO),
                )
                best = DetectedCard(corners=corners, confidence=confidence)
                best_area = rect_area

        return best

    @staticmethod
    def _order_corners(
        pts: np.ndarray,
    ) -> tuple[tuple[float, float], ...]:
        """4点を TL, TR, BR, BL の順に並べ替える。"""
        s = pts.sum(axis=1)
        diff = pts[:, 1] - pts[:, 0]  # y - x

        tl = pts[int(np.argmin(s))]
        br = pts[int(np.argmax(s))]
        tr = pts[int(np.argmin(diff))]
        bl = pts[int(np.argmax(diff))]

        return (
            (float(tl[0]), float(tl[1])),
            (float(tr[0]), float(tr[1])),
            (float(br[0]), float(br[1])),
            (float(bl[0]), float(bl[1])),
        )
