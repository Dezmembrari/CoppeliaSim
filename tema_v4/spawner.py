import random
import config

class Spawner:
    def __init__(self, sim, target_spacing=0.5):
        self.sim = sim
        self.target_spacing = target_spacing
        self.accumulated_dist = 0.9 
        self.last_sim_time = self.sim.getSimulationTime()
        
        # --- THE FIX: Load handles dynamically from config.py ---
        self.templates = []
        for path, name in config.PATHS["spawner_templates"]:
            self.templates.append((self.sim.getObject(path), name))
            
        self.spawn_point = self.sim.getObject(config.PATHS["spawn_point"])
        
        # Secure originals underground
        for handle, _ in self.templates:
            self.sim.setObjectPosition(handle, -1, [0, 0, -5])
            self.sim.setObjectInt32Param(handle, self.sim.shapeintparam_static, 1)
            
        print("[SPAWNER] Synced and Ready.")

    def update(self, now, current_speed):
        dt = now - self.last_sim_time
        self.last_sim_time = now

        # Only add distance if the belt is actually moving forward in time
        if dt > 0:
            self.accumulated_dist += abs(current_speed) * dt

        # Spawn logic
        if self.accumulated_dist >= self.target_spacing:
            choice_handle, obj_name = random.choice(self.templates)
            
            # Clone and Place
            new_obj = self.sim.copyPasteObjects([choice_handle], 0)[0]
            self.sim.setObjectQuaternion(new_obj, -1, [0, 0, 0, 1])
            spawn_pos = self.sim.getObjectPosition(self.spawn_point, -1)
            self.sim.setObjectPosition(new_obj, -1, spawn_pos)
            
            # Enable physics
            self.sim.setObjectInt32Param(new_obj, self.sim.shapeintparam_static, 0)
            self.sim.resetDynamicObject(new_obj)

            print(f"[SPAWNER] Distance Reached ({self.accumulated_dist:.2f}m). Spawned: {obj_name}")
            
            # Reset odometer
            self.accumulated_dist = 0