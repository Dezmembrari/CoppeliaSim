from actuators import fire_pusher, retract_pusher, set_conveyor_speed
from robot_controller import UR5Robot 

class Station:
    def __init__(self, sim, name, pusher_path, laser_path, short_belt_path, end_sensor_path, robot_base_path, targets, next_queue=None):
        self.sim = sim
        self.name = name
        
        # Hardware Setup
        self.pusher = self.sim.getObject(pusher_path)
        self.laser = self.sim.getObject(laser_path)
        self.short_belt = self.sim.getObject(short_belt_path)
        self.end_sensor = self.sim.getObject(end_sensor_path)
        
        # Delegate the robot completely to its own class
        self.robot = UR5Robot(sim, robot_base_path, name=f"{name} Arm")
        
        # Logic Setup
        self.targets = targets
        self.in_queue = []          
        self.next_queue = next_queue 
        self.robot_queue = []       
        
        # State Variables
        self.laser_cooldown = 0
        self.push_state = "IDLE"
        self.push_timer = 0
        self.belt_state = "RUNNING"
        self.short_speed = 0.1

    def update(self, now):
        requires_stop = False
        
        # =========================================================
        # 1. ROBOT DELEGATION & SHORT BELT LOGIC
        # (Evaluated FIRST so the Pusher knows the true belt status)
        # =========================================================
        robot_status = self.robot.update(now)
        r_res = self.sim.readProximitySensor(self.end_sensor)
        object_at_sensor = (r_res[0] > 0)
        
        if self.belt_state == "RUNNING":
            if object_at_sensor:
                self.belt_state = "WAITING_FOR_LIFT"
                set_conveyor_speed(self.sim, self.short_belt, 0.0) 
                
                shape = self.robot_queue[0] if self.robot_queue else "unknown"
                print(f"[{self.name}] Halting belt. Robot grabbing {shape.upper()}")
                physical_handle = r_res[3]
                self.robot.start_sort(shape, physical_handle, now)
            else:
                # FIX 2: Only run the short belt if an item is actively on it!
                if len(self.robot_queue) > 0:
                    set_conveyor_speed(self.sim, self.short_belt, self.short_speed)
                else:
                    set_conveyor_speed(self.sim, self.short_belt, 0.0)
                
        elif self.belt_state == "WAITING_FOR_LIFT":
            set_conveyor_speed(self.sim, self.short_belt, 0.0) 
            
            if robot_status in ["SWINGING", "DROPPING", "RETURNING"]:
                print(f"[{self.name}] Object lifted! Short belt cleared.")
                if self.robot_queue: self.robot_queue.pop(0)
                self.belt_state = "ROBOT_AWAY"
                
        elif self.belt_state == "ROBOT_AWAY":
            if object_at_sensor:
                # An item arrived at the end while the robot was away. Stop and wait!
                set_conveyor_speed(self.sim, self.short_belt, 0.0)
            else:
                # Keep moving to bring next item forward, or stop if empty
                if len(self.robot_queue) > 0:
                    set_conveyor_speed(self.sim, self.short_belt, self.short_speed)
                else:
                    set_conveyor_speed(self.sim, self.short_belt, 0.0)
                    
            if robot_status == "HOME":
                self.belt_state = "RUNNING"

        # =========================================================
        # 2. PUSHER LOGIC (Falling Edge)
        # =========================================================
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
            if not broken: 
                passed_obj = self.in_queue.pop(0)
                if self.next_queue is not None:
                    self.next_queue.append(passed_obj)
                    print(f"[{self.name}] Passed {passed_obj.upper()} downstream.")
                self.push_state = "IDLE"
                self.laser_cooldown = now + 0.3

        elif self.push_state == "TARGET_CROSSING":
            if not broken: 
                # FIX 1: The pusher can fire as long as the robot isn't actively 
                # grabbing (WAITING_FOR_LIFT) AND the short belt isn't physically jammed.
                if not object_at_sensor and self.belt_state != "WAITING_FOR_LIFT":
                    obj = self.in_queue.pop(0)
                    self.robot_queue.append(obj)
                    fire_pusher(self.sim, self.pusher)
                    self.push_state = "PUSHING"
                    self.push_timer = now + 1.2
                    # Kickstart the short belt so it receives the item smoothly
                    set_conveyor_speed(self.sim, self.short_belt, self.short_speed)
                else:
                    requires_stop = True # Target centered, but short belt is blocked. Halt main belt!

        elif self.push_state == "PUSHING":
            if now > self.push_timer:
                retract_pusher(self.sim, self.pusher)
                self.push_state = "IDLE"
                self.laser_cooldown = now + 0.3

        return requires_stop