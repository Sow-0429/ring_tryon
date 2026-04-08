from __future__ import annotations

from typing import Optional

import pytest

from app.domain.model.landmark import HandLandmarks, Point


def make_hand_landmarks(
    points: Optional[list[Point]] = None,
    handedness: str = "Right",
    confidence: float = 0.95,
) -> HandLandmarks:
    """テスト用のHandLandmarksを生成する。"""
    if points is None:
        # 正規化座標 (0-1) で21個のランドマークを配置
        # 手を広げた状態を模擬
        points = [
            Point(0.5, 0.9, 0.0),     # 0: WRIST
            Point(0.42, 0.78, 0.0),   # 1: THUMB_CMC
            Point(0.35, 0.68, 0.0),   # 2: THUMB_MCP
            Point(0.30, 0.58, 0.0),   # 3: THUMB_IP
            Point(0.26, 0.50, 0.0),   # 4: THUMB_TIP
            Point(0.40, 0.55, 0.0),   # 5: INDEX_MCP
            Point(0.40, 0.42, 0.0),   # 6: INDEX_PIP
            Point(0.40, 0.33, 0.0),   # 7: INDEX_DIP
            Point(0.40, 0.25, 0.0),   # 8: INDEX_TIP
            Point(0.48, 0.52, 0.0),   # 9: MIDDLE_MCP
            Point(0.48, 0.38, 0.0),   # 10: MIDDLE_PIP
            Point(0.48, 0.28, 0.0),   # 11: MIDDLE_DIP
            Point(0.48, 0.20, 0.0),   # 12: MIDDLE_TIP
            Point(0.56, 0.55, 0.0),   # 13: RING_MCP
            Point(0.56, 0.42, 0.0),   # 14: RING_PIP
            Point(0.56, 0.33, 0.0),   # 15: RING_DIP
            Point(0.56, 0.26, 0.0),   # 16: RING_TIP
            Point(0.63, 0.60, 0.0),   # 17: PINKY_MCP
            Point(0.63, 0.50, 0.0),   # 18: PINKY_PIP
            Point(0.63, 0.43, 0.0),   # 19: PINKY_DIP
            Point(0.63, 0.37, 0.0),   # 20: PINKY_TIP
        ]
    return HandLandmarks(points=points, handedness=handedness, confidence=confidence)
