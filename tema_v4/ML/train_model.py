import os
import cv2
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# --- CONFIGURATION ---
# 1. Automatically find the folder where this script lives (the ML folder)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. Build absolute paths based on the script's location
DATASET_DIR = os.path.join(SCRIPT_DIR, "dataset")
MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, "random_forest_model.joblib")
IMAGE_SIZE = (128, 128) # Force all images to this size for mathematical consistency


def get_fingerprint(img):
    """
    Core mathematical extractor. Separated so main.py can use it live!
    """
    img = cv2.resize(img, IMAGE_SIZE)

    # 1. Color
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
    cv2.normalize(hist, hist)
    color_features = hist.flatten()

    # 2. Shape 
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. CHANGE THIS: Update the HOG window to match the 128x128 image
    hog = cv2.HOGDescriptor((128,128), (16,16), (8,8), (8,8), 9)
    shape_features = hog.compute(gray).flatten()

    return np.hstack((color_features, shape_features))
    
def extract_features(image_path):
    """ Reads an image from the hard drive and extracts features. """
    img = cv2.imread(image_path)
    if img is None:
        return None
    return get_fingerprint(img)

def load_data():
    """
    Crawls the dataset directory, extracts features, and assigns labels.
    """
    X = [] # This will hold the feature arrays (the fingerprints)
    y = [] # This will hold the text labels (e.g., "red_cube")

    print(f"Scanning dataset in: {DATASET_DIR}...")
    
    # Get all the folder names (which act as our class labels)
    classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]
    
    for label in classes:
        folder_path = os.path.join(DATASET_DIR, label)
        images = os.listdir(folder_path)
        print(f"Processing '{label}': {len(images)} images found.")
        
        for image_name in images:
            image_path = os.path.join(folder_path, image_name)
            features = extract_features(image_path)
            
            if features is not None:
                X.append(features)
                y.append(label)
                
    return np.array(X), np.array(y)

def main():
    # 1. Load and process the data
    X, y = load_data()
    
    if len(X) == 0:
        print("Error: No valid images found. Check your dataset folders.")
        return

    print(f"\nSuccessfully extracted features from {len(X)} total images.")
    print(f"Each image was reduced to an array of {len(X[0])} numbers.")

    # 2. Split data into Training and Testing sets
    # We use 80% to teach the model, and hold back 20% to test if it actually learned
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Initialize and Train the Random Forest
    print("\nTraining the Random Forest model...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)

    # 4. Test the model's accuracy on the 20% it has never seen
    print("Testing model against holdout data...")
    predictions = rf_model.predict(X_test)
    
    accuracy = accuracy_score(y_test, predictions)
    print(f"\n--- MODEL RESULTS ---")
    print(f"Overall Accuracy: {accuracy * 100:.2f}%\n")
    print(classification_report(y_test, predictions))

    # 5. Save the brain to disk
    joblib.dump(rf_model, MODEL_SAVE_PATH)
    print(f"Model successfully saved to: {MODEL_SAVE_PATH}")
    print("Training complete! You can now use this file in main.py to make live predictions.")

if __name__ == "__main__":
    main()