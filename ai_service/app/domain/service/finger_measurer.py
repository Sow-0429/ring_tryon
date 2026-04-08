from __future__ import annotations

import math
from statistics import median

import cv2
import numpy as np

from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import FingerMeasurement, Scale


class FingerMeasurer:
    MEASUREMENT_RATIOS = (0.25, 0.30, 0.35, 0.40, 0.45)

    def measure(
        self,
        image: np.ndarray,
        landmarks: HandLandmarks,
        scale: Scale,
        finger_name: str,
        length_mm: float,
    ) -> FingerMeasurement:
        h, w = image.shape[:2]

        mcp = landmarks.finger_mcp(finger_name)
        pip = landmarks.finger_pip(finger_name)

        mcp_px = mcp.pixel_coords(w, h)
        pip_px = pip.pixel_coords(w, h)

        dx = pip_px[0] - mcp_px[0]
        dy = pip_px[1] - mcp_px[1]
        finger_angle = math.atan2(dy, dx)
        mcp_pip_dist = math.hypot(dx, dy)

        scan_length = int(max(30, min(300, mcp_pip_dist * 1.2)))

        widths: list[float] = []
        for ratio in self.MEASUREMENT_RATIOS:
            rx = mcp_px[0] + dx * ratio
            ry = mcp_px[1] + dy * ratio
            w_px = self._measure_width_at_point(
                image, rx, ry, finger_angle, scan_length,
            )
            widths.append(w_px)

        width_px = self._robust_median(widths)

        ring_ratio = 0.35
        ring_x = mcp_px[0] + dx * ring_ratio
        ring_y = mcp_px[1] + dy * ring_ratio
        width_mm = scale.px_to_mm(width_px)

        return FingerMeasurement(
            finger_name=finger_name,
            length_mm=length_mm,
            width_px=width_px,
            width_mm=width_mm,
            ring_position_x=ring_x,
            ring_position_y=ring_y,
            finger_angle_rad=finger_angle,
        )

    def _robust_median(self, values: list[float]) -> float:
        """外れ値を除去した中央値を返す。MADベースのフィルタリング。"""
        if len(values) <= 2:
            return median(values)

        med = median(values)
        deviations = [abs(v - med) for v in values]
        mad = median(deviations)

        if mad == 0:
            return med

        filtered = [v for v, d in zip(values, deviations) if d <= 1.5 * mad]
        return median(filtered) if filtered else med

    def _measure_width_at_point(
        self,
        image: np.ndarray,
        cx: float,
        cy: float,
        finger_angle: float,
        scan_length: int,
    ) -> float:
        width = self._measure_canny(image, cx, cy, finger_angle, scan_length)
        if width is not None:
            return width
        return self._measure_gradient(image, cx, cy, finger_angle, scan_length)

    def _measure_canny(
        self,
        image: np.ndarray,
        cx: float,
        cy: float,
        finger_angle: float,
        scan_length: int,
    ) -> float | None:
        """Cannyエッジ検出ベースの幅測定。適応的閾値を使用。"""
        perp_angle = finger_angle + math.pi / 2
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        med_val = float(np.median(gray))
        low_thresh = max(0, int(0.66 * med_val))
        high_thresh = min(255, int(1.33 * med_val))
        edges = cv2.Canny(gray, low_thresh, high_thresh)

        left_edge = None
        right_edge = None

        for t in range(-scan_length, scan_length + 1):
            sx = int(cx + t * math.cos(perp_angle))
            sy = int(cy + t * math.sin(perp_angle))
            if 0 <= sx < image.shape[1] and 0 <= sy < image.shape[0]:
                if edges[sy, sx] > 0:
                    if t < 0 and (left_edge is None or t > left_edge):
                        left_edge = t
                    elif t >= 0 and right_edge is None:
                        right_edge = t

        if left_edge is not None and right_edge is not None:
            width = abs(right_edge - left_edge)
            if width >= 5:
                return float(width)
        return None

    def _measure_gradient(
        self,
        image: np.ndarray,
        cx: float,
        cy: float,
        finger_angle: float,
        scan_length: int,
    ) -> float:
        """フォールバック: 勾配ベースのエッジ検出。"""
        perp_angle = finger_angle + math.pi / 2
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        samples = []
        for t in range(-scan_length, scan_length + 1):
            sx = int(cx + t * math.cos(perp_angle))
            sy = int(cy + t * math.sin(perp_angle))
            if 0 <= sx < image.shape[1] and 0 <= sy < image.shape[0]:
                samples.append((t, int(blurred[sy, sx])))

        if len(samples) < 10:
            return float(scan_length) * 0.3

        values = np.array([s[1] for s in samples], dtype=np.float64)
        gradient = np.gradient(values)
        abs_gradient = np.abs(gradient)

        center_idx = len(samples) // 2
        left_edge = center_idx
        right_edge = center_idx
        threshold = np.max(abs_gradient) * 0.3

        for i in range(center_idx, -1, -1):
            if abs_gradient[i] > threshold:
                left_edge = i
                break

        for i in range(center_idx, len(samples)):
            if abs_gradient[i] > threshold:
                right_edge = i
                break

        width_px = abs(samples[right_edge][0] - samples[left_edge][0])
        return max(width_px, 5.0)
