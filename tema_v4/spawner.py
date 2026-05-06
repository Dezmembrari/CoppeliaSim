import time
import random
from coppeliasim_zmqremoteapi_client import RemoteAPIClient

def main():
    print("Connecting Spawner to CoppeliaSim...")
    client = RemoteAPIClient()
    sim = client.require('sim')

    # --- 1. GET HANDLES ---
    try:
        template_red = sim.getObject('/Red_cuboid')
        template_blue = sim.getObject('/Blue_cuboid')
        spawn_point = sim.getObject('/Spawn_point')
        print("Templates and Spawn Point found!")
    except Exception as e:
        print("Error finding objects. Check names in the hierarchy:", e)
        return

    # Wait a moment to ensure the simulation is fully running (started by main.py)
    time.sleep(2)
    
    spawn_interval = 10.0  # Seconds between each cube dropping

    print(f"Spawner active! Dropping a cube every {spawn_interval} seconds...")

    # --- 2. MAIN SPAWN LOOP ---
    try:
        while True:
            # Check if simulation is stopped
            if sim.getSimulationState() == sim.simulation_stopped:
                print("Simulation stopped. Exiting spawner.")
                break

            # Pick a random template
            choice = random.choice([template_red, template_blue])
            color_name = "RED" if choice == template_red else "BLUE"

            # 1. Copy the template (returns a list of new handles, we want the first one)
            new_cube = sim.copyPasteObjects([choice], 0)[0]

            # 2. Get the XYZ coordinates of the Spawn_Point (-1 means absolute world coordinates)
            spawn_pos = sim.getObjectPosition(spawn_point, -1)

            # 3. Teleport the newly copied cube to the Spawn_Point
            sim.setObjectPosition(new_cube, -1, spawn_pos)

            # Activates the object so it falls on the conveyor
            sim.resetDynamicObject(new_cube)

            print(f"Spawned a {color_name} cube!")

            # Wait before spawning the next one
            time.sleep(spawn_interval)
            
    except KeyboardInterrupt:
        print("\nSpawner manually stopped.")

if __name__ == "__main__":
    main()