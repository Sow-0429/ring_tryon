from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.application.analyze_hand_usecase import (
    AnalyzeHandUsecase,
    CardNotDetectedError,
    CoinNotDetectedError,
    HandNotDetectedError,
    LowQualityImageError,
)
from app.domain.model.calibration import (
    CalibrationInput,
    CardCalibrationInput,
    CoinCalibrationInput,
    FingerCalibrationInput,
)
from app.domain.model.measurement import RingSize
from app.interfaces.dependencies import get_analyze_hand_usecase
from app.interfaces.image_converter import decode_upload_image

router = APIRouter()


def _build_calibration_input(
    middle_finger_length_mm: float | None,
    use_coin: bool,
    use_card: bool,
) -> CalibrationInput:
    selected = sum([middle_finger_length_mm is not None, use_coin, use_card])
    if selected != 1:
        raise HTTPException(
            status_code=422,
            detail=(
                "Specify exactly one calibration method: "
                "middle_finger_length_mm, use_coin=true, or use_card=true"
            ),
        )
    if use_coin:
        return CoinCalibrationInput()
    if use_card:
        return CardCalibrationInput()
    return FingerCalibrationInput(middle_finger_length_mm=middle_finger_length_mm)


class FingerSizeResponse(BaseModel):
    length_mm: float
    width_mm: float
    base_width_mm: float
    pip_width_mm: float
    circumference_mm: float
    ring_size_jp: int
    ring_size_jp_range: tuple[int, int]
    ring_size_us: float
    ring_size_eu: int
    ring_position_x: float
    ring_position_y: float
    finger_angle_deg: float


class AnalyzeHandResponse(BaseModel):
    pixels_per_mm: float
    calibration_method: str
    handedness: str
    confidence: float
    fingers: dict[str, FingerSizeResponse]


@router.post("/api/analyze-hand", response_model=AnalyzeHandResponse)
async def analyze_hand(
    image: UploadFile = File(...),
    middle_finger_length_mm: float | None = Form(None),
    use_coin: bool = Form(False),
    use_card: bool = Form(False),
) -> AnalyzeHandResponse:
    calibration_input = _build_calibration_input(
        middle_finger_length_mm, use_coin, use_card,
    )

    img = await decode_upload_image(image)
    usecase = get_analyze_hand_usecase()

    try:
        result = usecase.execute(img, calibration_input)
    except HandNotDetectedError:
        raise HTTPException(status_code=422, detail="No hand detected in image")
    except LowQualityImageError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "low_quality_image",
                "messages": e.messages,
            },
        )
    except CoinNotDetectedError:
        raise HTTPException(
            status_code=422,
            detail="No coin detected. Place a 100-yen coin next to your hand.",
        )
    except CardNotDetectedError:
        raise HTTPException(
            status_code=422,
            detail="No card detected. Place a credit/IC card next to your hand.",
        )

    fingers = {}
    for name, finger in result.fingers.items():
        fingers[name] = FingerSizeResponse(
            length_mm=round(finger.measurement.length_mm, 2),
            width_mm=round(finger.measurement.width_mm, 2),
            base_width_mm=round(finger.measurement.base_width_mm, 2),
            pip_width_mm=round(finger.measurement.pip_width_mm, 2),
            circumference_mm=round(finger.ring_size.circumference_mm, 2),
            ring_size_jp=finger.ring_size.jp_size,
            ring_size_jp_range=finger.ring_size.jp_size_range,
            ring_size_us=finger.ring_size.us_size,
            ring_size_eu=finger.ring_size.eu_size,
            ring_position_x=round(finger.measurement.ring_position_x, 1),
            ring_position_y=round(finger.measurement.ring_position_y, 1),
            finger_angle_deg=round(finger.measurement.finger_angle_deg, 1),
        )

    return AnalyzeHandResponse(
        pixels_per_mm=round(result.scale.pixels_per_mm, 4),
        calibration_method=result.calibration_method,
        handedness=result.landmarks.handedness,
        confidence=round(result.landmarks.confidence, 4),
        fingers=fingers,
    )


class ScanFingerResponse(BaseModel):
    length_mm: float
    base_width_mm: float
    pip_width_mm: float
    width_mm: float
    circumference_mm: float
    ring_size_jp: int
    ring_size_jp_range: tuple[int, int]
    ring_size_us: float
    ring_size_eu: int


class ConfidenceResponse(BaseModel):
    value: float
    agreement: float
    frame_coverage: float
    quality_ratio: float


class AnalyzeScanResponse(BaseModel):
    pixels_per_mm: float
    calibration_method: str
    handedness: str
    total_frames: int
    accepted_frames: int
    confidence: ConfidenceResponse | None
    fingers: dict[str, ScanFingerResponse]


@router.post("/api/analyze-hand-scan", response_model=AnalyzeScanResponse)
async def analyze_hand_scan(
    images: list[UploadFile] = File(...),
    middle_finger_length_mm: float | None = Form(None),
    use_coin: bool = Form(False),
    use_card: bool = Form(False),
) -> AnalyzeScanResponse:
    """指スキャン(複数フレーム)を中央値集約して号数と信頼度を返す。"""
    calibration_input = _build_calibration_input(
        middle_finger_length_mm, use_coin, use_card,
    )

    frames = [await decode_upload_image(img) for img in images]
    usecase = get_analyze_hand_usecase()

    try:
        result = usecase.execute_scan(frames, calibration_input)
    except LowQualityImageError as e:
        raise HTTPException(
            status_code=422,
            detail={"error": "low_quality_image", "messages": e.messages},
        )

    session = result.session
    fingers = {}
    for name, summary in session.fingers.items():
        ring_size = RingSize(circumference_mm=summary.circumference_mm)
        fingers[name] = ScanFingerResponse(
            length_mm=round(summary.measurement.length_mm, 2),
            base_width_mm=round(summary.measurement.base_width_mm, 2),
            pip_width_mm=round(summary.measurement.pip_width_mm, 2),
            width_mm=round(summary.measurement.width_mm, 2),
            circumference_mm=round(summary.circumference_mm, 2),
            ring_size_jp=ring_size.jp_size,
            ring_size_jp_range=ring_size.jp_size_range,
            ring_size_us=ring_size.us_size,
            ring_size_eu=ring_size.eu_size,
        )

    confidence = None
    if session.confidence is not None:
        confidence = ConfidenceResponse(
            value=round(session.confidence.value, 4),
            agreement=round(session.confidence.agreement, 4),
            frame_coverage=round(session.confidence.frame_coverage, 4),
            quality_ratio=round(session.confidence.quality_ratio, 4),
        )

    return AnalyzeScanResponse(
        pixels_per_mm=round(session.pixels_per_mm, 4),
        calibration_method=session.calibration_method,
        handedness=session.handedness,
        total_frames=result.total_frames,
        accepted_frames=result.accepted_frames,
        confidence=confidence,
        fingers=fingers,
    )
