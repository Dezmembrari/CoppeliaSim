import time
import cv2
import numpy as np
import joblib
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# Import the AI logic and your actuator subprogram
from ML.train_model import get_fingerprint 
from actuators import fire_pusher

def ai_predict(sim, sensor_handle, model):
    """Takes a live picture and asks the AI what it sees, with a saturation check."""
    try:
        img, res = sim.getVisionSensorImg(sensor_handle)
        if not img or len(img) == 0:
            return "NONE"

        img = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        img = cv2.flip(img, 0)

        # Skip the AI if the image is mostly gray (empty belt/pusher)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        if np.mean(hsv[:, :, 1]) < 40: 
            return "NONE"

        features = get_fingerprint(img)
        prediction = model.predict([features])[0]
        return prediction
    except Exception:
        return "NONE"

def main():
    print("Connecting to CoppeliaSim...")
    client = RemoteAPIClient()
    sim = client.require('sim')

    # --- 1. SETUP HANDLES FOR ALL 4 STATIONS ---
    try:
        # Dictionary to store our station components for easy iteration
        stations = {
            "red_cube": {
                "cam": sim.getObject('/visionSensor'),
                "pusher": sim.getObject('/Joint_pusher'),
                "last_fire": 0
            },
            "blue_cube": {
                "cam": sim.getObject('/visionSensor_2'),
                "pusher": sim.getObject('/Joint_pusher_2'),
                "last_fire": 0
            },
            "red_cylinder": {
                "cam": sim.getObject('/visionSensor_3'),
                "pusher": sim.getObject('/Joint_pusher_3'),
                "last_fire": 0
            },
            "blue_cylinder": {
                "cam": sim.getObject('/visionSensor_4'),
                "pusher": sim.getObject('/Joint_pusher_4'),
                "last_fire": 0
            }
        }
        print("All 4 Vision Sensors and Pushers linked!")
    except Exception as e:
        print("Error finding objects. Check hierarchy names:", e)
        return

    # --- 2. LOAD THE AI BRAIN ---
    try:
        rf_model = joblib.load("ML/random_forest_model.joblib")
        print("AI Model Loaded Successfully!")
    except Exception as e:
        print(f"Failed to load AI model: {e}")
        return

    sim.startSimulation()
    hold_duration = 2.0 # Time the pusher stays extended

    try:
        while True:
            if sim.getSimulationState() == sim.simulation_stopped:
                break
            
            now = time.time()

            # --- LOOP THROUGH ALL 4 STATIONS ---
            for target_label, hardware in stations.items():
                
                # Only check the camera if the pusher isn't currently busy
                if now > hardware["last_fire"] + hold_duration + 0.5:
                    prediction = ai_predict(sim, hardware["cam"], rf_model)
                    
                    # If the AI sees EXACTLY what this station is designed to push
                    if prediction == target_label:
                        print(f"STATION {target_label}: MATCH! Firing pusher...")
                        
                        # Use your actuators.py subprogram!
                        # We pass 0.25m distance and 2.0s hold time
                        fire_pusher(sim, hardware["pusher"], 0.25, hold_duration)
                        
                        # Mark the time so we don't double-fire
                        hardware["last_fire"] = now

            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nSorting line stopped.")

if __name__ == "__main__":
    main()