from coppeliasim_zmqremoteapi_client import RemoteAPIClient
# from vision_ml import load_ai_model, get_camera_state, ask_ai
from vision import get_camera_state
from ml_inference import load_ai_model, ask_ai
from actuators import set_conveyor_speed
from station_manager import Station
from spawner import Spawner
import config

def main():
    print("Connecting to CoppeliaSim...")
    client = RemoteAPIClient()
    sim = client.require('sim')
    client.setStepping(True) 

    try:
        main_belts = [sim.getObject('/conveyor_1'), sim.getObject('/conveyor_2'), sim.getObject('/conveyor_3')]
        master_cam = sim.getObject('/visionSensor')
        shutter_sensor = sim.getObject('/proximitySensor_5')

        st2 = Station(sim, "Station 2", '/Joint_pusher_2', '/proximitySensor_2', '/conveyor_5', '/proximitySensor_4', '/UR5_2', ["blue_cube", "blue_cylinder"])
        st1 = Station(sim, "Station 1", '/Joint_pusher', '/proximitySensor_1', '/conveyor_4', '/proximitySensor_3', '/UR5_1', ["red_cube", "red_cylinder"], next_queue=st2.in_queue)
        
        stations = [st1, st2]
        item_spawner = Spawner(sim, target_spacing=0.5)

    except Exception as e:
        print(f"Hardware missing: {e}"); return

    rf_model = load_ai_model()
    sim.startSimulation()
    
    MAIN_SPEED = 0.1
    shutter_last = False
    
    # --- THE CACHE VARIABLE ---
    current_main_speed = -1.0 

    print("\n[SYSTEM] Factory Online. Synchronous mode active.")

    try:
        while True:
            if sim.getSimulationState() == sim.simulation_stopped: break
            now = sim.getSimulationTime()
            
            # 1. AI SHUTTER
            res_s = sim.readProximitySensor(shutter_sensor)
            if res_s[0] > 0 and not shutter_last:
                img, _ = get_camera_state(sim, master_cam)
                prediction, _ = ask_ai(img, rf_model)
                print(f"\n[AI SCAN] {prediction.upper()} detected.")
                st1.in_queue.append(prediction) 
            shutter_last = (res_s[0] > 0)

            # 2. UPDATE STATIONS
            main_belt_force_stop = False
            for st in stations:
                if st.update(now):
                    main_belt_force_stop = True

            # 3. MASTER BELT COMMAND (Optimized)
            final_speed = 0.0 if main_belt_force_stop else MAIN_SPEED
            
            # --- THE FIX: Only send if speed actually changes ---
            if final_speed != current_main_speed:
                set_conveyor_speed(sim, main_belts, final_speed)
                sim.setFloatSignal('conveyorSpeed', final_speed)
                current_main_speed = final_speed

            # 4. UPDATE SPAWNER
            item_spawner.update(now, final_speed)

            # Step simulation
            client.step() 

    except KeyboardInterrupt: 
        print("\n[SYSTEM] Emergency Stop triggered...")
        try:
            rescue_client = RemoteAPIClient()
            rescue_sim = rescue_client.require('sim')
            rescue_client.setStepping(False) 
            rescue_sim.stopSimulation()
        except:
            pass

if __name__ == "__main__": 
    main()