from functools import lru_cache

from app.application.analyze_hand_usecase import AnalyzeHandUsecase
from app.domain.service.circumference_estimator import CircumferenceEstimator
from app.domain.service.finger_measurer import FingerMeasurer
from app.domain.service.scale_calibrator import ScaleCalibrator
from app.infrastructure.hand_detector import MediaPipeHandDetector


@lru_cache(maxsize=1)
def get_analyze_hand_usecase() -> AnalyzeHandUsecase:
    return AnalyzeHandUsecase(
        detector=MediaPipeHandDetector(),
        calibrator=ScaleCalibrator(),
        measurer=FingerMeasurer(),
        estimator=CircumferenceEstimator(),
    )
