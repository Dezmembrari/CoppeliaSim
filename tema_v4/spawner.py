import time
import random
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

def main():
    print("Connecting Spawner to CoppeliaSim...")
    client = RemoteAPIClient()
    sim = client.require('sim')

    # --- 1. GET HANDLES ---
    try:
        # Added the cuboid templates alongside the cylinders
        template_red_cyl = sim.getObject('/Red_cylinder')
        template_blue_cyl = sim.getObject('/Blue_cylinder')
        template_red_cube = sim.getObject('/Red_cuboid')
        template_blue_cube = sim.getObject('/Blue_cuboid')
        spawn_point = sim.getObject('/Spawn_point')
        print("Templates and Spawn Point found!")
    except Exception as e:
        print("Error finding objects. Check names in the hierarchy:", e)
        return

    # Wait a moment to ensure the simulation is fully running (started by main.py)
    time.sleep(2)
    
    spawn_interval = 10.0  # Seconds between each object dropping

    print(f"Spawner active! Dropping an object every {spawn_interval} seconds...")

    # Group the handles with a descriptive name for easy random selection and logging
    templates = [
        (template_red_cyl, "RED CYLINDER"),
        (template_blue_cyl, "BLUE CYLINDER"),
        (template_red_cube, "RED CUBOID"),
        (template_blue_cube, "BLUE CUBOID")
    ]

    # --- 2. MAIN SPAWN LOOP ---
    try:
        while True:
            # Check if simulation is stopped
            if sim.getSimulationState() == sim.simulation_stopped:
                print("Simulation stopped. Exiting spawner.")
                break

            # Pick a random template tuple (unpacks the handle and the name)
            choice_handle, obj_name = random.choice(templates)

            # 1. Copy the template (returns a list of new handles, we want the first one)
            new_object = sim.copyPasteObjects([choice_handle], 0)[0]

            # 2. Get the XYZ coordinates of the Spawn_Point (-1 means absolute world coordinates)
            spawn_pos = sim.getObjectPosition(spawn_point, -1)

            # 3. Teleport the newly copied object to the Spawn_Point
            sim.setObjectPosition(new_object, -1, spawn_pos)

            # Activates the object so it falls on the conveyor
            sim.resetDynamicObject(new_object)

            print(f"Spawned a {obj_name}!")

            # Wait before spawning the next one
            time.sleep(spawn_interval)
            
    except KeyboardInterrupt:
        print("\nSpawner manually stopped.")

if __name__ == "__main__":
    main()