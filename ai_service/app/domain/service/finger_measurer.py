import math

import cv2
import numpy as np

from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import FingerMeasurement, Scale


class FingerMeasurer:
    RING_POSITION_RATIO = 0.35

    def measure(
        self,
        image: np.ndarray,
        landmarks: HandLandmarks,
        scale: Scale,
        finger_name: str,
    ) -> FingerMeasurement:
        h, w = image.shape[:2]

        mcp = landmarks.finger_mcp(finger_name)
        pip = landmarks.finger_pip(finger_name)

        mcp_px = mcp.pixel_coords(w, h)
        pip_px = pip.pixel_coords(w, h)

        ring_x = mcp_px[0] + (pip_px[0] - mcp_px[0]) * self.RING_POSITION_RATIO
        ring_y = mcp_px[1] + (pip_px[1] - mcp_px[1]) * self.RING_POSITION_RATIO

        dx = pip_px[0] - mcp_px[0]
        dy = pip_px[1] - mcp_px[1]
        finger_angle = math.atan2(dy, dx)

        width_px = self._measure_width_at_point(image, ring_x, ring_y, finger_angle)
        width_mm = scale.px_to_mm(width_px)

        return FingerMeasurement(
            finger_name=finger_name,
            width_px=width_px,
            width_mm=width_mm,
            ring_position_x=ring_x,
            ring_position_y=ring_y,
            finger_angle_rad=finger_angle,
        )

    def _measure_width_at_point(
        self,
        image: np.ndarray,
        cx: float,
        cy: float,
        finger_angle: float,
        scan_length: int = 100,
    ) -> float:
        perp_angle = finger_angle + math.pi / 2

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        samples = []
        for t in range(-scan_length, scan_length + 1):
            sx = int(cx + t * math.cos(perp_angle))
            sy = int(cy + t * math.sin(perp_angle))
            if 0 <= sx < image.shape[1] and 0 <= sy < image.shape[0]:
                samples.append((t, int(blurred[sy, sx])))

        if len(samples) < 10:
            return self._fallback_width(scan_length)

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

    def _fallback_width(self, scan_length: int) -> float:
        return float(scan_length) * 0.3
