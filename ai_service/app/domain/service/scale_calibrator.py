from app.domain.model.landmark import HandLandmarks
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
        tip = landmarks.middle_finger_tip
        pixel_distance = mcp.distance_to(tip, image_width, image_height)

        if pixel_distance == 0:
            raise ValueError("Middle finger landmarks overlap; cannot compute scale")

        pixels_per_mm = pixel_distance / middle_finger_length_mm
        return Scale(pixels_per_mm=pixels_per_mm)
