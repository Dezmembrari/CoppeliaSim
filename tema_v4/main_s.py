import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

# Import your newly created modules!
from vision import get_dominant_color, save_snapshot
from actuators import fire_pusher

def main():
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
        return # Exit the function gracefully

    # --- 2. START SIMULATION ---
    print("Starting simulation...")
    sim.startSimulation()
    print("System running. Waiting for cubes...")


    red_fire_time = 0
    blue_fire_time = 0
    hold_duration = 5.0 # How long to stay extended
    cube_under_cam_red = False
    cube_under_cam_blue = False

    # --- 3. MAIN CONTROL LOOP ---
    try:
        while True:
            # Clean exit if simulation is stopped manually in software
            if sim.getSimulationState() == sim.simulation_stopped:
                print("Simulation stopped by user. Exiting script.")
                break

            #assures async functionality
            now = time.time()

            # Note: We pass 'sim' into our functions now!
            # Read Red Camera
            # if get_dominant_color(sim, cam_red) == "RED":
            #     print("Red cube detected! Firing Pusher 1...")
            #     # Update this line: 0.25 meters, 2.0 seconds hold
            #     fire_pusher(sim, pusher_red, extend_distance=0.25, hold_time=2.0)
            #     time.sleep(0.5) 
            color_red = get_dominant_color(sim, cam_red)
            if color_red == "RED":
                if not cube_under_cam_red:
                    # OBJECT JUST ARRIVED! Take picture and fire pusher.
                    cube_under_cam_red = True
                    save_snapshot(sim, cam_red, label="red_cylinder") # <-- Data collection!
                    
                    if now > red_fire_time + hold_duration:
                        print("Red Detected! Firing pusher...")
                        sim.setJointTargetPosition(pusher_red, 0.25)
                        red_fire_time = now # Mark the start time
            else:
                # The belt is empty again, reset the flag
                cube_under_cam_red = False
                
            # Read Blue Camera
            # if get_dominant_color(sim, cam_blue) == "BLUE":
            #     print("Blue cube detected! Firing Pusher 2...")
            #     # Update this line: 0.25 meters, 2.0 seconds hold
            #     fire_pusher(sim, pusher_blue, extend_distance=0.25, hold_time=2.0)
            #     time.sleep(0.5)
            color_blue = get_dominant_color(sim, cam_blue)
            if color_blue == "BLUE":
                if not cube_under_cam_blue:
                    # OBJECT JUST ARRIVED! Take picture and fire pusher.
                    cube_under_cam_blue = True
                    save_snapshot(sim, cam_blue, label="blue_cylinder") # <-- Data collection!
                    
                    if now > blue_fire_time + hold_duration:
                        print("Blue Detected! Firing pusher...")
                        sim.setJointTargetPosition(pusher_blue, 0.25)
                        blue_fire_time = now
            else:
                # The belt is empty again, reset the flag
                cube_under_cam_blue = False
            
            # Automatically pull back after the duration has passed
            if red_fire_time > 0 and now > red_fire_time + hold_duration:
                sim.setJointTargetPosition(pusher_red, 0.0)
            
            if blue_fire_time > 0 and now > blue_fire_time + hold_duration:
                sim.setJointTargetPosition(pusher_blue, 0.0)
            
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        # Handles what happens if you press Ctrl+C in your terminal
        print("\nScript manually interrupted by user.")

# Standard Python safety guard
if __name__ == "__main__":
    main()