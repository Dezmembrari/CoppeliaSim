import random
import config

class Spawner:
    def __init__(self, sim, target_spacing=0.5):
        self.sim = sim
        self.target_spacing = target_spacing # Default spacing
        self.accumulated_dist = 0.9 
        self.last_sim_time = self.sim.getSimulationTime()
        
        self.template_map = {}
        for path, name in config.PATHS["spawner_templates"]:
            handle = self.sim.getObject(path)
            self.template_map[name] = handle
            self.sim.setObjectPosition(handle, -1, [0, 0, -5])
            self.sim.setObjectInt32Param(handle, self.sim.shapeintparam_static, 1)

        self.spawn_point = self.sim.getObject(config.PATHS["spawn_point"])

    def update(self, now, current_speed, auto_enabled, manual_queue, target_spacing):
        """Now accepts target_spacing as an argument to allow real-time changes."""
        dt = now - self.last_sim_time
        self.last_sim_time = now

        if dt > 0:
            self.accumulated_dist += abs(current_speed) * dt

        # The check now uses the dynamic target_spacing for both auto and manual modes
        if self.accumulated_dist >= target_spacing:
            target_handle = None
            obj_name = ""

            if manual_queue:
                obj_name = manual_queue.pop(0)
                target_handle = self.template_map.get(obj_name)
            
            elif auto_enabled:
                obj_name, target_handle = random.choice(list(self.template_map.items()))

            if target_handle:
                new_obj = self.sim.copyPasteObjects([target_handle], 0)[0]
                spawn_pos = self.sim.getObjectPosition(self.spawn_point, -1)
                self.sim.setObjectPosition(new_obj, -1, spawn_pos)
                self.sim.setObjectInt32Param(new_obj, self.sim.shapeintparam_static, 0)
                self.sim.resetDynamicObject(new_obj)
                
                self.accumulated_dist = 0
                return f"Spawner: Placed {obj_name} on line."
        return None