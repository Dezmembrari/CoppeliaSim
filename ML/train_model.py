import os
import cv2
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")
MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, "random_forest_model.joblib")

def get_fingerprint(img):
    """Extracts 4 rotation-proof features: Hue, Saturation, Circularity, Extent."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    
    # Find the shape outline
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return np.zeros(4)
        
    c = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(c)
    perimeter = cv2.arcLength(c, True)
    
    # Feature 1: Circularity (1.0 = Circle, ~0.78 = Square, regardless of rotation)
    circularity = 0
    if perimeter > 0:
        circularity = (4 * np.pi * area) / (perimeter * perimeter)
        
    # Feature 2: Extent (Area divided by Bounding Box Area)
    x, y, w, h = cv2.boundingRect(c)
    rect_area = w * h
    extent = area / rect_area if rect_area > 0 else 0
    
    # Features 3 & 4: Mean Color (Only looking at the object, ignoring the black)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(mask, [c], -1, 255, -1)
    
    mean_color = cv2.mean(hsv, mask=mask)
    mean_hue = mean_color[0]
    mean_sat = mean_color[1]

    return np.array([mean_hue, mean_sat, circularity, extent])

def extract_features(image_path):
    img = cv2.imread(image_path)
    if img is None: return None
    return get_fingerprint(img)

def load_data():
    X, y = [], []
    classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]
    for label in classes:
        folder_path = os.path.join(DATASET_DIR, label)
        for image_name in os.listdir(folder_path):
            features = extract_features(os.path.join(folder_path, image_name))
            if features is not None:
                X.append(features)
                y.append(label)
    return np.array(X), np.array(y)

def main():
    X, y = load_data()
    if len(X) == 0: return
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    predictions = rf_model.predict(X_test)
    
    print(f"\n--- MODEL RESULTS ---")
    print(f"Overall Accuracy: {accuracy_score(y_test, predictions) * 100:.2f}%")
    print(classification_report(y_test, predictions))
    
    joblib.dump(rf_model, MODEL_SAVE_PATH)
    print(f"Model saved to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    main()