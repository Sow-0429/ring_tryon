from app.domain.model.landmark import HandLandmarks, LandmarkIndex
from app.domain.model.measurement import Scale


class ScaleCalibrator:
    def calibrate(
        self,
        landmarks: HandLandmarks,
        middle_finger_length_mm: float,
        image_width: int,
        image_height: int,
    ) -> Scale:
        mcp = landmarks.middle_finger_mcp
        pip = landmarks.get(LandmarkIndex.MIDDLE_FINGER_PIP)
        dip = landmarks.get(LandmarkIndex.MIDDLE_FINGER_DIP)
        tip = landmarks.middle_finger_tip

        pixel_distance = (
            mcp.distance_to_3d(pip, image_width, image_height)
            + pip.distance_to_3d(dip, image_width, image_height)
            + dip.distance_to_3d(tip, image_width, image_height)
        )

        if pixel_distance == 0:
            raise ValueError("Middle finger landmarks overlap; cannot compute scale")

        pixels_per_mm = pixel_distance / middle_finger_length_mm
        return Scale(pixels_per_mm=pixels_per_mm)
