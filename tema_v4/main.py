import time
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from vision_ml import load_ai_model, get_camera_state, ask_ai
from actuators import set_conveyor_speed
from station_manager import Station

def main():
    print("Connecting to CoppeliaSim...")
    client = RemoteAPIClient()
    sim = client.require('sim')

    # --- THE MAGIC BULLET: Enable Synchronous Mode ---
    client.setStepping(True) 

    try:
        main_belts = [sim.getObject('/conveyor_1'), sim.getObject('/conveyor_2'), sim.getObject('/conveyor_3')]
        master_cam = sim.getObject('/visionSensor')
        shutter_sensor = sim.getObject('/proximitySensor_5')

        # --- INITIALIZE MODULAR STATIONS ---
        # Note: We initialize ST2 first so we can pass its input queue to ST1!
        st2 = Station(sim, "Station 2", '/Joint_pusher_2', '/proximitySensor_2', '/conveyor_5', '/proximitySensor_4', '/UR5_2', ["blue_cube", "blue_cylinder"])
        st1 = Station(sim, "Station 1", '/Joint_pusher', '/proximitySensor_1', '/conveyor_4', '/proximitySensor_3', '/UR5_1', ["red_cube", "red_cylinder"], next_queue=st2.in_queue)
        
        stations = [st1, st2]

    except Exception as e:
        print(f"Hardware missing: {e}"); return

    rf_model = load_ai_model()
    sim.startSimulation()
    
    MAIN_SPEED = 0.1
    shutter_last = False

    print("\n[SYSTEM] Factory Online. Synchronous mode active.")

    try:
        while True:
            if sim.getSimulationState() == sim.simulation_stopped: break
            now = sim.getSimulationTime()
            
            # =================================================================
            # 1. THE AI SHUTTER
            # =================================================================
            res_s = sim.readProximitySensor(shutter_sensor)
            if res_s[0] > 0 and not shutter_last:
                img, _ = get_camera_state(sim, master_cam)
                prediction, _ = ask_ai(img, rf_model)
                print(f"\n[AI SCAN] {prediction.upper()} detected. Entering line.")
                
                # Directly feed the AI output into Station 1's queue
                st1.in_queue.append(prediction) 
            shutter_last = (res_s[0] > 0)

            # =================================================================
            # 2. UPDATE STATIONS
            # =================================================================
            main_belt_force_stop = False
            for st in stations:
                # The station updates itself and returns True if it needs the belt to stop
                if st.update(now):
                    main_belt_force_stop = True

            # =================================================================
            # 3. MASTER BELT COMMAND
            # =================================================================
            final_speed = 0.0 if main_belt_force_stop else MAIN_SPEED
            set_conveyor_speed(sim, main_belts, final_speed)
            sim.setFloatSignal('conveyorSpeed', final_speed)

            # --- THE MAGIC BULLET 2: Step the simulation ---
            client.step() 
            
            # (time.sleep(0.01) was removed. In synchronous mode, client.step() 
            # tells the physics engine to advance exactly one frame, acting as our perfect loop timer.)

    except KeyboardInterrupt: 
        print("\n[SYSTEM] Emergency Stop triggered. Releasing physics engine...")
        try:
            # Our main ZMQ socket is jammed because we interrupted it mid-receive.
            # We open a fresh "rescue" connection to safely shut down the server.
            rescue_client = RemoteAPIClient()
            rescue_sim = rescue_client.require('sim')
            
            rescue_client.setStepping(False) 
            rescue_sim.stopSimulation()
            print("[SYSTEM] Safely disconnected.")
        except Exception as e:
            print(f"[SYSTEM] Rescue failed: {e}. Please press the STOP button in CoppeliaSim.")

if __name__ == "__main__": 
    main()