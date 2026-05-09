import cv2
import numpy as np

def get_fingerprint(img):
    """
    Extracts geometric and color features from an image.
    Must be perfectly identical to the logic used during model training!
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours: 
        return np.zeros(4)
        
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    
    circularity = 0
    if perimeter > 0:
        circularity = (4 * np.pi * area) / (perimeter * perimeter)
        
    x, y, w, h = cv2.boundingRect(c)
    rect_area = w * h
    extent = area / rect_area if rect_area > 0 else 0
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(mask, [c], -1, 255, -1)
    
    mean_color = cv2.mean(hsv, mask=mask)
    return np.array([mean_color[0], mean_color[1], circularity, extent])

def get_camera_state(sim, sensor_handle):
    """
    Captures an image from CoppeliaSim and finds the object's vertical center.
    Returns: (OpenCV Image, center_y_integer)
    """
    
    """
    Captures an image from CoppeliaSim. 
    NOTE: Performance is optimized for a 128x128 sensor resolution.
    Higher resolutions will significantly increase ZMQ network lag.
    """
    
    img, res = sim.getVisionSensorImg(sensor_handle)
    if not img or len(img) == 0:
        return None, None

    img = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.flip(img, 0)

    # Threshold to ignore the dark belt background
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    
    coords = cv2.findNonZero(thresh)
    if coords is None:
        return img, None
        
    x, y, w, h = cv2.boundingRect(coords)
    center_y = int(y + (h / 2))

    return img, center_y