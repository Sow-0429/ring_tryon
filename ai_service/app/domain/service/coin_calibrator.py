from app.domain.model.measurement import Scale
from app.domain.model.reference_object import COIN_100_YEN_DIAMETER_MM, DetectedCoin


class CoinCalibrator:
    def calibrate(self, detected: DetectedCoin) -> Scale:
        pixels_per_mm = detected.diameter_px / COIN_100_YEN_DIAMETER_MM
        return Scale(pixels_per_mm=pixels_per_mm)
