import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

print("Connecting to CoppeliaSim...")
client = RemoteAPIClient()
sim = client.require('sim')

# --- 1. GET HANDLES ---
try:
    cam_red = sim.getObject('/visionSensor')
    cam_blue = sim.getObject('/visionSensor_2')
    
    pusher_red = sim.getObject('/Joint_pusher')
    pusher_blue = sim.getObject('/Joint_pusher_2')
    print("All sensors and pushers found!")
except Exception as e:
    print("Error finding objects. Check names in the hierarchy:", e)
    exit()

# --- 2. HELPER FUNCTIONS ---
def fire_pusher(joint_handle, extend_distance=0.5, hold_time=1.0):
    sim.setJointTargetPosition(joint_handle, extend_distance)
    time.sleep(hold_time)
    sim.setJointTargetPosition(joint_handle, 0.0)

def get_dominant_color(sensor_handle):
    # Wrap this in a try-except just in case the camera glitches
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
        pass
        
    return "NONE"

# --- 3. START SIMULATION FROM PYTHON ---
print("Starting simulation...")
sim.startSimulation()

print("System running. Waiting for cubes...")

# --- 4. MAIN CONTROL LOOP ---
while True:
    # Safety check: if you press the "Stop" square in CoppeliaSim, this ends the Python script cleanly
    if sim.getSimulationState() == sim.simulation_stopped:
        print("Simulation stopped by user. Exiting script.")
        break

    # Read Red Camera
    if get_dominant_color(cam_red) == "RED":
        print("Red cube detected! Firing Pusher 1...")
        fire_pusher(pusher_red)
        time.sleep(0.5) 
        
    # Read Blue Camera
    if get_dominant_color(cam_blue) == "BLUE":
        print("Blue cube detected! Firing Pusher 2...")
        fire_pusher(pusher_blue)
        time.sleep(0.5)
        
    # Crucial: tiny sleep so we don't spam the ZMQ server and crash the network
    time.sleep(0.05)