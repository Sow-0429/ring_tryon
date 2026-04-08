from functools import lru_cache

from app.application.analyze_hand_usecase import AnalyzeHandUsecase
from app.domain.service.circumference_estimator import CircumferenceEstimator
from app.domain.service.coin_calibrator import CoinCalibrator
from app.domain.service.finger_length_measurer import FingerLengthMeasurer
from app.domain.service.finger_measurer import FingerMeasurer
from app.domain.service.scale_calibrator import ScaleCalibrator
from app.infrastructure.coin_detector import CoinDetector
from app.infrastructure.hand_detector import MediaPipeHandDetector


@lru_cache(maxsize=1)
def get_analyze_hand_usecase() -> AnalyzeHandUsecase:
    return AnalyzeHandUsecase(
        detector=MediaPipeHandDetector(),
        calibrator=ScaleCalibrator(),
        coin_detector=CoinDetector(),
        coin_calibrator=CoinCalibrator(),
        measurer=FingerMeasurer(),
        length_measurer=FingerLengthMeasurer(),
        estimator=CircumferenceEstimator(),
    )
