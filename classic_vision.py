import cv2
import numpy as np

def ask_classic(img):
    """
    Evaluates image using explicit OpenCV thresholds.
    Returns: (prediction_string, confidence_float)
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 1. Color Masking
    lower_red1, upper_red1 = np.array([0, 100, 50]), np.array([10, 255, 255])
    lower_red2, upper_red2 = np.array([160, 100, 50]), np.array([180, 255, 255])
    mask_red = cv2.bitwise_or(cv2.inRange(hsv, lower_red1, upper_red1), cv2.inRange(hsv, lower_red2, upper_red2))

    lower_blue, upper_blue = np.array([100, 150, 0]), np.array([140, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    red_px = cv2.countNonZero(mask_red)
    blue_px = cv2.countNonZero(mask_blue)

    active_mask = None
    color = "unknown"
    if red_px > blue_px and red_px > 50:
        color = "red"
        active_mask = mask_red
    elif blue_px > red_px and blue_px > 50:
        color = "blue"
        active_mask = mask_blue
    else:
        return "unknown", 0.0

    # 2. Shape Detection (Extent Analysis)
    contours, _ = cv2.findContours(active_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return f"{color}_unknown", 50.0

    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    x, y, w, h = cv2.boundingRect(c)
    
    if w * h == 0:
        return f"{color}_unknown", 50.0

    extent = area / (w * h)
    
    # A top-down square has an extent of ~1.0. A circle has an extent of ~0.785.
    shape = "cube" if extent > 0.88 else "cylinder"

    return f"{color}_{shape}", 100.0