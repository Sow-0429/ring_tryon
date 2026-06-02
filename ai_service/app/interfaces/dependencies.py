import os
from functools import lru_cache

from app.application.analyze_hand_usecase import AnalyzeHandUsecase
from app.domain.service.card_calibrator import CardCalibrator
from app.domain.service.circumference_estimator import (
    TIER_PREMIUM,
    CircumferenceEstimator,
    DepthBasedCircumferenceEstimator,
    EllipseFitCircumferenceEstimator,
)
from app.domain.service.circumference_regression import (
    CircumferenceRegressionModel,
    RegressionCircumferenceEstimator,
)
from app.domain.service.coin_calibrator import CoinCalibrator
from app.domain.service.finger_length_measurer import FingerLengthMeasurer
from app.domain.service.finger_measurer import FingerMeasurer
from app.domain.service.frame_aggregator import FrameAggregator
from app.domain.service.quality_gate import QualityGate
from app.domain.service.scale_calibrator import ScaleCalibrator
from app.infrastructure.card_detector import CardDetector
from app.infrastructure.coin_detector import CoinDetector
from app.infrastructure.hand_detector import MediaPipeHandDetector
from app.infrastructure.hand_segmenter import HandSegmenter

CALIBRATION_MODEL_PATH = os.environ.get("CALIBRATION_MODEL_PATH", "")


def _build_estimator_selector():
    """ティア→推定戦略の選択器を構築する。

    standard: 較正済み回帰モデルがあれば回帰、無ければ固定比楕円近似。
    premium : 深度実測の楕円近似。
    課金判定(誰がpremiumか)は Go アプリ層(ADR-0008)。
    """
    standard: CircumferenceEstimator = EllipseFitCircumferenceEstimator()
    if CALIBRATION_MODEL_PATH and os.path.exists(CALIBRATION_MODEL_PATH):
        model = CircumferenceRegressionModel.load(CALIBRATION_MODEL_PATH)
        standard = RegressionCircumferenceEstimator(model)

    premium: CircumferenceEstimator = DepthBasedCircumferenceEstimator()

    def select(tier: str) -> CircumferenceEstimator:
        if tier == TIER_PREMIUM:
            return premium
        return standard

    return select


@lru_cache(maxsize=1)
def get_analyze_hand_usecase() -> AnalyzeHandUsecase:
    return AnalyzeHandUsecase(
        detector=MediaPipeHandDetector(),
        calibrator=ScaleCalibrator(),
        coin_detector=CoinDetector(),
        coin_calibrator=CoinCalibrator(),
        card_detector=CardDetector(),
        card_calibrator=CardCalibrator(),
        quality_gate=QualityGate(),
        segmenter=HandSegmenter(),
        measurer=FingerMeasurer(),
        length_measurer=FingerLengthMeasurer(),
        estimator_selector=_build_estimator_selector(),
        aggregator=FrameAggregator(),
    )
