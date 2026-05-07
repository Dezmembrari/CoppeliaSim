import cv2
import numpy as np
import joblib

def load_ai_model(model_path="ML/random_forest_model.joblib"):
    try:
        model = joblib.load(model_path)
        return model
    except Exception as e:
        print(f"❌ Failed to load AI model: {e}")
        return None

def get_fingerprint(img):
    """Must be perfectly identical to train_model.py!"""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours: return np.zeros(4)
        
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
    """Simply finds the object and returns the image and its exact Y-center."""
    img, res = sim.getVisionSensorImg(sensor_handle)
    if not img or len(img) == 0:
        return None, None

    img = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = cv2.flip(img, 0)

    # Use a threshold of 20 to ignore the dark conveyor belt and only see the bright objects
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 20, 255, cv2.THRESH_BINARY)
    
    coords = cv2.findNonZero(thresh)
    
    if coords is None:
        return img, None
        
    x, y, w, h = cv2.boundingRect(coords)
    
    # Calculate the exact center of the object's mass
    center_y = int(y + (h / 2))

    # Return the Image FIRST, and the center_y integer SECOND
    return img, center_y

def ask_ai(img, model):
    features = get_fingerprint(img)
    prediction = model.predict([features])[0]
    
    probabilities = model.predict_proba([features])[0]
    confidence = max(probabilities) * 100
    
    return prediction, confidence