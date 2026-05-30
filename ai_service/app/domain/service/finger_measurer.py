from __future__ import annotations

import math
from statistics import median

import numpy as np

from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import FingerMeasurement, Scale


class FingerMeasurer:
    """手シルエットのマスクから指幅を測る。

    指軸(MCP→PIP)に垂直な走査線上で、中心点を含むマスクTrueの連続区間を
    指幅とする。背景や照明に依存するエッジ走査は使わない。
    指輪が通過する付け根(MCP寄り)とPIP関節の両方を測り、号数を決める
    最大円周(=最大幅)となる方を採用する。
    """

    # MCP→PIP を 0.0(MCP)〜1.0(PIP) としたときの計測比率。
    # 付け根は水かきを避けて少し遠位、PIPは関節付近。
    BASE_RATIOS = (0.20, 0.27, 0.34)
    PIP_RATIOS = (0.88, 0.96, 1.04)

    def measure(
        self,
        mask: np.ndarray,
        landmarks: HandLandmarks,
        scale: Scale,
        finger_name: str,
        length_mm: float,
    ) -> FingerMeasurement:
        h, w = mask.shape[:2]

        mcp_px = landmarks.finger_mcp(finger_name).pixel_coords(w, h)
        pip_px = landmarks.finger_pip(finger_name).pixel_coords(w, h)

        dx = pip_px[0] - mcp_px[0]
        dy = pip_px[1] - mcp_px[1]
        finger_angle = math.atan2(dy, dx)
        mcp_pip_dist = math.hypot(dx, dy)
        scan_length = int(max(20, min(200, mcp_pip_dist)))

        base_width_px, base_pos = self._region_width(
            mask, mcp_px, dx, dy, finger_angle, scan_length, self.BASE_RATIOS,
        )
        pip_width_px, pip_pos = self._region_width(
            mask, mcp_px, dx, dy, finger_angle, scan_length, self.PIP_RATIOS,
        )

        base_width_mm = scale.px_to_mm(base_width_px)
        pip_width_mm = scale.px_to_mm(pip_width_px)

        if pip_width_px >= base_width_px:
            width_px, ring_pos = pip_width_px, pip_pos
        else:
            width_px, ring_pos = base_width_px, base_pos

        return FingerMeasurement(
            finger_name=finger_name,
            length_mm=length_mm,
            width_px=width_px,
            width_mm=scale.px_to_mm(width_px),
            ring_position_x=ring_pos[0],
            ring_position_y=ring_pos[1],
            finger_angle_rad=finger_angle,
            base_width_mm=base_width_mm,
            pip_width_mm=pip_width_mm,
        )

    def _region_width(
        self,
        mask: np.ndarray,
        mcp_px: tuple[float, float],
        dx: float,
        dy: float,
        finger_angle: float,
        scan_length: int,
        ratios: tuple[float, ...],
    ) -> tuple[float, tuple[float, float]]:
        """指定比率群でマスク幅を測り、外れ値除去した中央値と代表位置を返す。"""
        widths: list[float] = []
        positions: list[tuple[float, float]] = []
        for ratio in ratios:
            cx = mcp_px[0] + dx * ratio
            cy = mcp_px[1] + dy * ratio
            width = self._mask_width_at_point(
                mask, cx, cy, finger_angle, scan_length,
            )
            if width is not None:
                widths.append(width)
                positions.append((cx, cy))

        if not widths:
            mid = len(ratios) // 2
            cx = mcp_px[0] + dx * ratios[mid]
            cy = mcp_px[1] + dy * ratios[mid]
            return 0.0, (cx, cy)

        width = self._robust_median(widths)
        return width, positions[len(positions) // 2]

    def _mask_width_at_point(
        self,
        mask: np.ndarray,
        cx: float,
        cy: float,
        finger_angle: float,
        scan_length: int,
    ) -> float | None:
        """走査線(指軸に垂直)上で中心を含むマスクTrueの連続区間長を返す。

        中心がマスク外なら、走査線上で最も近いTrue画素をシードに採り直す。
        どの画素もTrueでなければ None。
        """
        perp = finger_angle + math.pi / 2
        h, w = mask.shape[:2]

        def sample(t: int) -> bool:
            sx = int(round(cx + t * math.cos(perp)))
            sy = int(round(cy + t * math.sin(perp)))
            if 0 <= sx < w and 0 <= sy < h:
                return bool(mask[sy, sx])
            return False

        seed = 0
        if not sample(0):
            seed = None
            for d in range(1, scan_length + 1):
                if sample(d):
                    seed = d
                    break
                if sample(-d):
                    seed = -d
                    break
            if seed is None:
                return None

        right = seed
        while right + 1 <= scan_length and sample(right + 1):
            right += 1
        left = seed
        while left - 1 >= -scan_length and sample(left - 1):
            left -= 1

        return float(right - left + 1)

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
