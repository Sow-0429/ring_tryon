from app.domain.model.landmark import HandLandmarks
from app.domain.model.measurement import Scale


class FingerLengthMeasurer:
    """各指のMCP→PIP→DIP→TIPの関節経由距離(mm)を算出する。"""

    def measure(
        self,
        landmarks: HandLandmarks,
        scale: Scale,
        finger_name: str,
        image_width: int,
        image_height: int,
    ) -> float:
        mcp = landmarks.finger_mcp(finger_name)
        pip = landmarks.finger_pip(finger_name)
        dip = landmarks.finger_dip(finger_name)
        tip = landmarks.finger_tip(finger_name)

        segment_px = (
            mcp.distance_to_3d(pip, image_width, image_height)
            + pip.distance_to_3d(dip, image_width, image_height)
            + dip.distance_to_3d(tip, image_width, image_height)
        )
        return scale.px_to_mm(segment_px)
