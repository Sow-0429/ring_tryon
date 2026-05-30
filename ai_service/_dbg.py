import cv2
import numpy as np

from tests.test_card_detector import _make_image_with_card

img = _make_image_with_card()
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
blur = cv2.GaussianBlur(gray, (5, 5), 0)
t, binary = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
out = ["otsu %s shape %s" % (t, img.shape)]
for name, mask in (("binary", binary), ("inv", cv2.bitwise_not(binary))):
    cnts = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    out.append("%s n=%d" % (name, len(cnts)))
    for c in cnts:
        a = cv2.contourArea(c)
        peri = cv2.arcLength(c, True)
        ap = cv2.approxPolyDP(c, 0.02 * peri, True)
        pts = ap.reshape(-1, 2).tolist()
        out.append("  area=%d verts=%d pts=%s" % (int(a), len(ap), pts))
with open("/tmp/d2.log", "w") as f:
    f.write("\n".join(out))
print("written")
