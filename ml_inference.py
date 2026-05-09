import joblib
from vision import get_fingerprint

def load_ai_model(model_path="ML/random_forest_model.joblib"):
    """Loads the pre-trained Scikit-Learn model."""
    try:
        model = joblib.load(model_path)
        print(f"[ML] Model loaded successfully from {model_path}")
        return model
    except Exception as e:
        print(f"[ML] ❌ Failed to load AI model: {e}")
        return None

def ask_ai(img, model):
    """
    Feeds an image through the feature extractor and the ML model.
    Returns: (prediction_string, confidence_float)
    """
    if model is None:
        return "unknown", 0.0
        
    # Translate image to numbers using the Vision module
    features = get_fingerprint(img)
    
    prediction = model.predict([features])[0]
    
    # Calculate confidence percentage
    probabilities = model.predict_proba([features])[0]
    confidence = max(probabilities) * 100
    
    return prediction, confidence