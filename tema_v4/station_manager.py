from actuators import set_conveyor_speed
from robot_controller import UR5Robot 
from pusher_controller import PusherController # <-- NEW IMPORT
import config

class Station:
    def __init__(self, sim, name, pusher_path, laser_path, short_belt_path, end_sensor_path, robot_base_path, targets, next_queue=None):
        self.sim = sim
        self.name = name
        
        # Hardware Setup
        self.laser = self.sim.getObject(laser_path)
        self.short_belt = self.sim.getObject(short_belt_path)
        self.end_sensor = self.sim.getObject(end_sensor_path)
        
        # Specialized Controllers
        self.robot = UR5Robot(sim, robot_base_path, name=f"{name} Arm")
        self.pusher_ctrl = PusherController(sim, pusher_path) # <-- REPLACED HANDLE
        
        # Logic Setup
        self.targets = targets
        self.in_queue = []          
        self.next_queue = next_queue 
        self.robot_queue = []       
        
        # Logic States (Object Tracking only)
        self.push_state = "IDLE"
        self.belt_state = "RUNNING"
        self.short_speed = config.SHORT_BELT_SPEED
        self.current_belt_speed = -1.0 

    def _apply_short_belt_speed(self, target_speed):
        if self.current_belt_speed != target_speed:
            set_conveyor_speed(self.sim, self.short_belt, target_speed)
            self.current_belt_speed = target_speed

    def update(self, now):
        requires_stop = False
        
        # 1. Advance Sub-Controllers
        robot_status = self.robot.update(now)
        self.pusher_ctrl.update(now) # <-- NEW: Advances mechanical state
        
        r_res = self.sim.readProximitySensor(self.end_sensor)
        object_at_sensor = (r_res[0] > 0)
        
        # =========================================================
        # 2. SHORT BELT LOGIC
        # =========================================================
        if self.belt_state == "RUNNING":
            if object_at_sensor:
                self.belt_state = "WAITING_FOR_LIFT"
                self._apply_short_belt_speed(0.0) 
                shape = self.robot_queue[0] if self.robot_queue else "unknown"
                self.robot.start_sort(shape, r_res[3], now)
            else:
                self._apply_short_belt_speed(self.short_speed if self.robot_queue else 0.0)
                
        elif self.belt_state == "WAITING_FOR_LIFT":
            self._apply_short_belt_speed(0.0) 
            if robot_status in ["SWINGING", "SWINGING_HIGH", "PLUNGING", "SETTLING", "PAUSE_DROP", "LIFTING_CLEAR", "RETURNING"]:
                if self.robot_queue: self.robot_queue.pop(0)
                self.belt_state = "ROBOT_AWAY"
                
        elif self.belt_state == "ROBOT_AWAY":
            self._apply_short_belt_speed(0.0 if object_at_sensor else (self.short_speed if self.robot_queue else 0.0))
            if robot_status == "HOME":
                self.belt_state = "RUNNING"

        # =========================================================
        # 3. SORTER LOGIC (Object Detection & Hand-off)
        # =========================================================
        res = self.sim.readProximitySensor(self.laser)
        broken = (res[0] > 0)

        # We only look for new items if the pusher is physically ready (IDLE)
        if self.push_state == "IDLE":
            if broken and self.in_queue and not self.pusher_ctrl.is_busy():
                obj = self.in_queue[0]
                self.push_state = "TARGET_CROSSING" if obj in self.targets else "PASSING"
        
        elif self.push_state == "PASSING":
            if not broken: 
                passed_obj = self.in_queue.pop(0)
                if self.next_queue is not None:
                    self.next_queue.append(passed_obj)
                self.push_state = "IDLE"

        elif self.push_state == "TARGET_CROSSING":
            if not broken: 
                # Check if short belt can accept the item
                if not object_at_sensor and self.belt_state != "WAITING_FOR_LIFT":
                    # TRIGGER PUSH
                    if self.pusher_ctrl.fire(now):
                        obj = self.in_queue.pop(0)
                        self.robot_queue.append(obj)
                        self.push_state = "IDLE" # Sorter logic returns to IDLE immediately
                        self._apply_short_belt_speed(self.short_speed)
                else:
                    requires_stop = True

        return requires_stop