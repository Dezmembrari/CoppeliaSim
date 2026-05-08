from actuators import fire_pusher, retract_pusher
import config

class PusherController:
    def __init__(self, sim, pusher_path):
        self.sim = sim
        self.handle = self.sim.getObject(pusher_path)
        
        # Mechanical States: IDLE, EXTENDING, COOLDOWN
        self.state = "IDLE"
        self.timer = 0

    def is_busy(self):
        """Returns True if the pusher is physically moving or cooling down."""
        return self.state != "IDLE"

    def fire(self, now):
        """Triggers the push sequence if the hardware is ready."""
        if self.state == "IDLE":
            fire_pusher(self.sim, self.handle)
            self.state = "EXTENDING"
            self.timer = now + config.PUSH_DURATION_SEC
            return True
        return False

    def update(self, now):
        """Advances the mechanical state machine based on time."""
        if self.state == "EXTENDING":
            if now > self.timer:
                retract_pusher(self.sim, self.handle)
                self.state = "COOLDOWN"
                self.timer = now + config.LASER_COOLDOWN_SEC
                
        elif self.state == "COOLDOWN":
            if now > self.timer:
                self.state = "IDLE"