import cv2
import numpy as np
from fastapi import UploadFile


async def decode_upload_image(upload: UploadFile) -> np.ndarray:
    contents = await upload.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
