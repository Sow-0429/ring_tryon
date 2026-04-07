import os

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

from app.domain.model.landmark import HandLandmarks, Point

MODEL_PATH = os.environ.get(
    "HAND_LANDMARKER_MODEL_PATH",
    "/app/models/hand_landmarker.task",
)


class MediaPipeHandDetector:
    def __init__(self, model_path: str = MODEL_PATH) -> None:
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = HandLandmarker.create_from_options(options)

    def detect(self, image: np.ndarray) -> HandLandmarks | None:
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=image)
        result = self._landmarker.detect(mp_image)

        if not result.hand_landmarks:
            return None

        raw_landmarks = result.hand_landmarks[0]
        handedness = result.handedness[0][0].category_name
        confidence = result.handedness[0][0].score

        points = [
            Point(x=lm.x, y=lm.y, z=lm.z)
            for lm in raw_landmarks
        ]

        return HandLandmarks(
            points=points,
            handedness=handedness,
            confidence=confidence,
        )
