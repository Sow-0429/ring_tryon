from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


class LandmarkIndex(IntEnum):
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_PIP = 6
    INDEX_FINGER_DIP = 7
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_MCP = 9
    MIDDLE_FINGER_PIP = 10
    MIDDLE_FINGER_DIP = 11
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_MCP = 13
    RING_FINGER_PIP = 14
    RING_FINGER_DIP = 15
    RING_FINGER_TIP = 16
    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20


@dataclass(frozen=True)
class Point:
    x: float
    y: float
    z: float = 0.0

    def pixel_coords(self, image_width: int, image_height: int) -> tuple[float, float]:
        return self.x * image_width, self.y * image_height

    def distance_to(self, other: Point, image_width: int, image_height: int) -> float:
        px1, py1 = self.pixel_coords(image_width, image_height)
        px2, py2 = other.pixel_coords(image_width, image_height)
        return ((px1 - px2) ** 2 + (py1 - py2) ** 2) ** 0.5


@dataclass(frozen=True)
class HandLandmarks:
    points: list[Point]
    handedness: str
    confidence: float

    def __post_init__(self) -> None:
        if len(self.points) != 21:
            raise ValueError(f"Expected 21 landmarks, got {len(self.points)}")

    def get(self, index: LandmarkIndex) -> Point:
        return self.points[index]

    @property
    def middle_finger_mcp(self) -> Point:
        return self.get(LandmarkIndex.MIDDLE_FINGER_MCP)

    @property
    def middle_finger_tip(self) -> Point:
        return self.get(LandmarkIndex.MIDDLE_FINGER_TIP)

    def finger_mcp(self, finger_name: str) -> Point:
        mapping = {
            "index": LandmarkIndex.INDEX_FINGER_MCP,
            "middle": LandmarkIndex.MIDDLE_FINGER_MCP,
            "ring": LandmarkIndex.RING_FINGER_MCP,
            "pinky": LandmarkIndex.PINKY_MCP,
        }
        return self.get(mapping[finger_name])

    def finger_pip(self, finger_name: str) -> Point:
        mapping = {
            "index": LandmarkIndex.INDEX_FINGER_PIP,
            "middle": LandmarkIndex.MIDDLE_FINGER_PIP,
            "ring": LandmarkIndex.RING_FINGER_PIP,
            "pinky": LandmarkIndex.PINKY_PIP,
        }
        return self.get(mapping[finger_name])

    def finger_tip(self, finger_name: str) -> Point:
        mapping = {
            "index": LandmarkIndex.INDEX_FINGER_TIP,
            "middle": LandmarkIndex.MIDDLE_FINGER_TIP,
            "ring": LandmarkIndex.RING_FINGER_TIP,
            "pinky": LandmarkIndex.PINKY_TIP,
        }
        return self.get(mapping[finger_name])
