import time
import random
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

def main():
    print("Connecting Motion-Aware Spawner...")
    client = RemoteAPIClient()
    sim = client.require('sim')

    try:
        # Handles for templates
        templates = [
            (sim.getObject('/Red_cylinder'), "RED CYLINDER"),
            (sim.getObject('/Blue_cylinder'), "BLUE CYLINDER"),
            (sim.getObject('/Red_cuboid'), "RED CUBOID"),
            (sim.getObject('/Blue_cuboid'), "BLUE CUBOID")
        ]
        spawn_point = sim.getObject('/Spawn_point')
        
        # We monitor this conveyor to see if we are moving
        main_conveyor = sim.getObject('/conveyor_1')

        # Secure originals underground
        for handle, _ in templates:
            sim.setObjectPosition(handle, -1, [0, 0, -5])
            sim.setObjectInt32Param(handle, sim.shapeintparam_static, 1)
            
        print("Spawner Synced with Conveyor Motion.")
    except Exception as e:
        print("Error during setup:", e); return

    # --- SPAWN CONFIGURATION ---
    target_spacing = 0.5  # Meters between objects
    accumulated_dist = 0.9 # Start almost ready to spawn the first one
    last_sim_time = sim.getSimulationTime()

    try:
        while True:
            if sim.getSimulationState() == sim.simulation_stopped: break

            # 1. Calculate Delta Time (Sim Time)
            now = sim.getSimulationTime()
            dt = now - last_sim_time
            last_sim_time = now

            # 2. Get Current Belt Velocity
            # We check the 'conveyorSpeed' signal usually set by actuators.py
            # Fallback: check the joint velocity directly if the signal isn't found
            speed = sim.getFloatSignal('conveyorSpeed')
            if speed is None:
                # Default to 0.1 if main.py is running, 0 if stopped
                # This is a fallback if your actuators.py doesn't use signals
                speed = 0.1 if dt > 0 else 0 
                # Note: To be 100% accurate, ensure actuators.py uses:
                # sim.setFloatSignal('conveyorSpeed', final_speed)

            # 3. Integrate Distance: Distance = Speed * Time
            # We only add distance if the belt is actually "on"
            if dt > 0:
                accumulated_dist += abs(speed) * dt

            # 4. Spawn logic
            if accumulated_dist >= target_spacing:
                choice_handle, obj_name = random.choice(templates)
                
                # Clone and Place
                new_obj = sim.copyPasteObjects([choice_handle], 0)[0]
                sim.setObjectQuaternion(new_obj, -1, [0, 0, 0, 1])
                spawn_pos = sim.getObjectPosition(spawn_point, -1)
                sim.setObjectPosition(new_obj, -1, spawn_pos)
                
                # Enable physics
                sim.setObjectInt32Param(new_obj, sim.shapeintparam_static, 0)
                sim.resetDynamicObject(new_obj)

                print(f"Distance Reached ({accumulated_dist:.2f}m). Spawned: {obj_name}")
                
                # Reset odometer
                accumulated_dist = 0
            
            # Small sleep to prevent CPU hogging, but keep it responsive
            time.sleep(0.01)
            
    except KeyboardInterrupt:
        print("\nSpawner offline.")

if __name__ == "__main__":
    main()