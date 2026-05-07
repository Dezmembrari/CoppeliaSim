from actuators import fire_pusher, retract_pusher, set_conveyor_speed

class Station:
    def __init__(self, sim, name, pusher_path, laser_path, short_belt_path, end_sensor_path, targets, next_queue=None):
        self.sim = sim
        self.name = name
        
        # Hardware Setup
        self.pusher = self.sim.getObject(pusher_path)
        self.laser = self.sim.getObject(laser_path)
        self.short_belt = self.sim.getObject(short_belt_path)
        self.end_sensor = self.sim.getObject(end_sensor_path)
        
        # Logic Setup
        self.targets = targets
        self.in_queue = []          # Items arriving here
        self.next_queue = next_queue # Where to send items that aren't ours
        self.robot_queue = []       # Items on the short belt
        
        # State Variables
        self.laser_cooldown = 0
        self.push_state = "IDLE"
        self.push_timer = 0
        self.belt_state = "RUNNING"
        self.belt_timer = 0
        self.short_speed = 0.1

    def update(self, now):
        """Runs the station logic and returns True if the main belt must be stopped."""
        requires_stop = False
        
        # --- 1. PUSHER LOGIC (Falling Edge) ---
        res = self.sim.readProximitySensor(self.laser)
        broken = (res[0] > 0)

        if self.push_state == "IDLE":
            if broken and self.in_queue and now > self.laser_cooldown:
                obj = self.in_queue[0]
                if obj in self.targets:
                    self.push_state = "TARGET_CROSSING"
                else:
                    self.push_state = "PASSING"
        
        elif self.push_state == "PASSING":
            if not broken: # Object fully cleared
                passed_obj = self.in_queue.pop(0)
                if self.next_queue is not None:
                    self.next_queue.append(passed_obj)
                    print(f"[{self.name}] Passed {passed_obj.upper()} downstream.")
                self.push_state = "IDLE"
                self.laser_cooldown = now + 0.3

        elif self.push_state == "TARGET_CROSSING":
            if not broken: # Object centered
                if self.belt_state == "RUNNING":
                    obj = self.in_queue.pop(0)
                    self.robot_queue.append(obj)
                    fire_pusher(self.sim, self.pusher)
                    self.push_state = "PUSHING"
                    self.push_timer = now + 1.2
                else:
                    requires_stop = True # Target centered, but robot busy

        elif self.push_state == "PUSHING":
            if now > self.push_timer:
                retract_pusher(self.sim, self.pusher)
                self.push_state = "IDLE"
                self.laser_cooldown = now + 0.3


        # --- 2. ROBOT & SHORT BELT LOGIC ---
        r_res = self.sim.readProximitySensor(self.end_sensor)
        
        if self.belt_state == "RUNNING":
            set_conveyor_speed(self.sim, self.short_belt, self.short_speed)
            if r_res[0] > 0:
                self.belt_state = "ROBOT_WORKING"
                self.belt_timer = now + 4.0 
                set_conveyor_speed(self.sim, self.short_belt, 0.0) 
                shape = self.robot_queue[0] if self.robot_queue else "Unknown"
                print(f"[{self.name} ROBOT] 🦾 Sorting: {shape.upper()}")
        
        elif self.belt_state == "ROBOT_WORKING":
            if now > self.belt_timer:
                if self.robot_queue: self.robot_queue.pop(0)
                self.belt_state = "CLEARING"
                self.belt_timer = now + 2.0
        
        elif self.belt_state == "CLEARING":
            set_conveyor_speed(self.sim, self.short_belt, self.short_speed)
            if now > self.belt_timer: 
                self.belt_state = "RUNNING"

        return requires_stop