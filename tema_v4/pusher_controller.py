from actuators import fire_pusher, retract_pusher

class PusherController:
    def __init__(self, sim, pusher_path, state):
        self.sim = sim
        self.gui_state = state # Shared state
        self.handle = self.sim.getObject(pusher_path)
        self.current_state = "IDLE"
        self.timer = 0

    def is_busy(self):
        return self.current_state != "IDLE"

    def fire(self, now):
        if self.current_state == "IDLE":
            fire_pusher(self.sim, self.handle)
            self.current_state = "EXTENDING"
            self.timer = now + self.gui_state.push_duration # Correct live-read
            return True
        return False

    def update(self, now):
        if self.current_state == "EXTENDING":
            if now > self.timer:
                retract_pusher(self.sim, self.handle)
                self.current_state = "COOLDOWN"
                self.timer = now + self.gui_state.laser_cooldown
        elif self.current_state == "COOLDOWN":
            if now > self.timer:
                self.current_state = "IDLE"