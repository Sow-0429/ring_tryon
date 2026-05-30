from app.domain.model.measurement import Scale
from app.domain.model.reference_object import (
    CARD_ID1_LONG_EDGE_MM,
    CARD_ID1_SHORT_EDGE_MM,
    DetectedCard,
)


class CardCalibrator:
    """検出したID-1カードからピクセル/mmスケールを算出する。

    長辺・短辺それぞれの推定値を平均し、片軸のノイズに対して頑健にする。
    """

    def calibrate(self, detected: DetectedCard) -> Scale:
        long_ppm = detected.long_edge_px / CARD_ID1_LONG_EDGE_MM
        short_ppm = detected.short_edge_px / CARD_ID1_SHORT_EDGE_MM
        pixels_per_mm = (long_ppm + short_ppm) / 2
        return Scale(pixels_per_mm=pixels_per_mm)
