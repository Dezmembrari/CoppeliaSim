import cv2
import numpy as np
import os
import time

def get_dominant_color(sim, sensor_handle):
    """Reads the camera and checks the center pixel for Red or Blue."""
    try:
        img, res = sim.getVisionSensorImg(sensor_handle)
        if not img or len(img) == 0:
            return "NONE"

        center_x = res[0] // 2
        center_y = res[1] // 2
        pixel_index = (center_y * res[0] + center_x) * 3

        r = img[pixel_index]
        g = img[pixel_index + 1]
        b = img[pixel_index + 2]

        if r > 150 and g < 100 and b < 100:
            return "RED"
        if b > 150 and r < 100 and g < 100:
            return "BLUE"
            
    except Exception:
        # Failsafe if the camera drops a frame
        pass
        
    return "NONE"

# To collect images for the dataset automagically 
def save_snapshot(sim, sensor_handle, label):
    """Grabs the current frame and saves it to ML/dataset/<label>"""
    try:
        img, res = sim.getVisionSensorImg(sensor_handle)
        
        # Convert to OpenCV format
        img = np.frombuffer(img, dtype=np.uint8).reshape(res[1], res[0], 3)
        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        img = cv2.flip(img, 0)

        # Ensure the directory exists
        save_dir = os.path.join("ML", "dataset", label)
        os.makedirs(save_dir, exist_ok=True)

        # Create a unique filename using a timestamp
        filename = f"img_{int(time.time() * 1000)}.png"
        save_path = os.path.join(save_dir, filename)
        
        cv2.imwrite(save_path, img)
        print(f"📸 Snapshot saved: {label}/{filename}")
        
    except Exception as e:
        print(f"Failed to save snapshot: {e}")