from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.application.analyze_hand_usecase import (
    AnalyzeHandUsecase,
    HandNotDetectedError,
)
from app.interfaces.dependencies import get_analyze_hand_usecase
from app.interfaces.image_converter import decode_upload_image

router = APIRouter()


class FingerSizeResponse(BaseModel):
    width_mm: float
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
    handedness: str
    confidence: float
    fingers: dict[str, FingerSizeResponse]


@router.post("/api/analyze-hand", response_model=AnalyzeHandResponse)
async def analyze_hand(
    image: UploadFile = File(...),
    middle_finger_length_mm: float = Form(...),
) -> AnalyzeHandResponse:
    img = await decode_upload_image(image)

    usecase = get_analyze_hand_usecase()

    try:
        result = usecase.execute(img, middle_finger_length_mm)
    except HandNotDetectedError:
        raise HTTPException(status_code=422, detail="No hand detected in image")

    fingers = {}
    for name, finger in result.fingers.items():
        fingers[name] = FingerSizeResponse(
            width_mm=round(finger.measurement.width_mm, 2),
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
        handedness=result.landmarks.handedness,
        confidence=round(result.landmarks.confidence, 4),
        fingers=fingers,
    )
