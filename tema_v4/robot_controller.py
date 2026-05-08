import math

class UR5Robot:
    def __init__(self, sim, base_path, name="Robot"):
        self.sim = sim
        self.name = name
        
        # 1. Hardware Setup
        self.joints = [self.sim.getObject(f"{base_path}/joint", {"index": i}) for i in range(6)]
        self.tip = self.sim.getObject(f"{base_path}/suctionPad")
        
        # Make the suction pad purely visual (Ghost it so it never pushes objects)
        self.sim.setObjectInt32Param(self.tip, self.sim.shapeintparam_respondable, 0)
        
        # 2. Extracted Joint Angles (Converted to Radians)
        self.pos_pickup      = self._deg2rad([0, 0, -67, -23, 90, 0])
        self.pos_hover       = self._calculate_vertical_lift(0.10) 
        
        # Home is now the safe Hover point to prevent sweeping the table
        self.pos_home        = self.pos_hover 
        
        self.pos_basket_cube = self._deg2rad([120, -20, -67, -3, 90, 0])
        self.pos_basket_cyl  = self._deg2rad([-160, -20, -67, -3, 90, 0])

        # 3. State Machine Variables
        self.state = "HOME"
        self.timer = 0
        self.current_target_shape = None
        self.held_object_handle = None 
        
        # 4. Trajectory Generation Variables
        self.is_moving = False
        self.move_start_time = 0
        self.move_duration = 1.0
        self.start_angles = [0]*6
        self.target_angles = [0]*6
        
        # 5. Snap to safe home instantly on startup (No trajectory needed for frame 0)
        for joint, angle in zip(self.joints, self.pos_home):
            self.sim.setJointTargetPosition(joint, angle)

    def _deg2rad(self, degrees_list):
        return [math.radians(d) for d in degrees_list]

    def _calculate_vertical_lift(self, lift_meters):
        """
        Robust Planar Inverse Kinematics for UR5.
        Calculates J2, J3, J4 to achieve a straight vertical lift while:
        1. Persisting the elbow configuration (up/down) from the pickup pose.
        2. Guarding against out-of-reach targets.
        3. Maintaining end-effector orientation."""
        L1 = 0.425   # Upper arm
        L2 = 0.3922  # Forearm
        
        # 1. Current state and configuration
        j2_init = self.pos_pickup[1]
        j3_init = self.pos_pickup[2]
        
        # Identify elbow configuration: -1 for elbow-up, 1 for elbow-down
        elbow_config = -1 if j3_init < 0 else 1
        
        # 2. Forward Kinematics: Map current joint state to Cartesian (X, Z)
        # Using the standard vertical-zero frame where J2=0 is UP.
        current_X = L1 * math.sin(j2_init) + L2 * math.sin(j2_init + j3_init)
        current_Z = L1 * math.cos(j2_init) + L2 * math.cos(j2_init + j3_init)
        
        # 3. Define Target (Lift Z, keep X locked)
        target_X = current_X
        target_Z = current_Z + lift_meters
        
        # 4. Inverse Kinematics
        D_sq = target_X**2 + target_Z**2
        D = math.sqrt(D_sq)
        
        # Reachability Guard
        if D > (L1 + L2) or D < abs(L1 - L2):
            print(f"[ROBOT] Target [{target_X:.3f}, {target_Z:.3f}] is out of reach!")
            return self.pos_pickup # Fallback to original pose to prevent crash

        # Solve for J3
        # Law of Cosines: D^2 = L1^2 + L2^2 - 2*L1*L2*cos(180 - J3) => cos(J3)
        cos_j3 = (D_sq - L1**2 - L2**2) / (2 * L1 * L2)
        cos_j3 = max(-1.0, min(1.0, cos_j3)) # Floating point safety
        
        # Apply elbow configuration persistence
        new_j3 = elbow_config * math.acos(cos_j3)
        
        # Solve for J2
        # Alpha: Angle to target | Beta: Internal triangle angle
        alpha = math.atan2(target_X, target_Z)
        beta = math.atan2(L2 * math.sin(new_j3), L1 + L2 * math.cos(new_j3))
        new_j2 = alpha - beta
        
        # 5. Orientation Constraint (J4)
        # Sum of angles relative to vertical must stay constant for level tool
        orig_sum = j2_init + j3_init + self.pos_pickup[3]
        new_j4 = orig_sum - (new_j2 + new_j3)
        
        # Construct final pose
        hover = list(self.pos_pickup)
        hover[1], hover[2], hover[3] = new_j2, new_j3, new_j4
        
        return hover

    # =========================================================
    # TRAJECTORY GENERATOR (Smooth, Anti-Flail Movement)
    # =========================================================
    def _start_move(self, target_angles, duration_sec, now):
        """Prepares a smooth transition from current angles to target angles"""
        self.start_angles = [self.sim.getJointPosition(j) for j in self.joints]
        self.target_angles = target_angles
        self.move_start_time = now
        self.move_duration = duration_sec
        self.is_moving = True

    def _update_movement(self, now):
        """Called every frame. Returns True if the move is finished."""
        if not self.is_moving: return True
        
        t = (now - self.move_start_time) / self.move_duration
        if t >= 1.0:
            t = 1.0
            self.is_moving = False
            
        # Cosine Easing (Slow start, fast middle, slow stop)
        ease_t = 0.5 * (1 - math.cos(math.pi * t))
        
        # Apply the micro-step to the motors
        for i in range(6):
            current_angle = self.start_angles[i] + (self.target_angles[i] - self.start_angles[i]) * ease_t
            self.sim.setJointTargetPosition(self.joints[i], current_angle)
            
        return not self.is_moving

    # =========================================================
    # THE GHOST GRIP
    # =========================================================
    def _set_gripper(self, active):
        if active and self.held_object_handle:
            self.sim.setObjectInt32Param(self.held_object_handle, self.sim.shapeintparam_respondable, 0)
            self.sim.setObjectInt32Param(self.held_object_handle, self.sim.shapeintparam_static, 1)
            self.sim.setObjectParent(self.held_object_handle, self.tip, True)

        elif not active and self.held_object_handle:
            self.sim.setObjectParent(self.held_object_handle, -1, True)
            self.sim.setObjectInt32Param(self.held_object_handle, self.sim.shapeintparam_static, 0)
            self.sim.setObjectInt32Param(self.held_object_handle, self.sim.shapeintparam_respondable, 1)
            self.sim.resetDynamicObject(self.held_object_handle)
            self.held_object_handle = None

    # =========================================================
    # SEQUENCER STATE MACHINE
    # =========================================================
    def start_sort(self, shape_name, object_handle, now):
        self.current_target_shape = shape_name
        self.held_object_handle = object_handle 
        
        # Because we rest at the safe Hover point, we go straight down to pickup
        self.state = "TO_PICKUP"
        self._start_move(self.pos_pickup, 0.6, now)

    def update(self, now):
        # Always run the movement interpolator first
        move_complete = self._update_movement(now)
        
        # If the arm is currently travelling, do nothing else
        if not move_complete: return self.state

        # State Machine Progresses ONLY when movement is finished
        if self.state == "TO_PICKUP":
            # Arrived at cube. Wait 0.4s before grabbing.
            self.state = "PAUSE_GRAB"
            self.timer = now + 0.4
            
        elif self.state == "PAUSE_GRAB":
            if now > self.timer:
                self._set_gripper(True) # ATTACH!
                self.state = "LIFTING"
                # Pull straight back up to hover over 0.6 seconds
                self._start_move(self.pos_hover, 0.6, now)
                
        elif self.state == "LIFTING":
            self.state = "SWINGING"
            # Swing to basket over 1.2 seconds
            if "cube" in self.current_target_shape.lower():
                self._start_move(self.pos_basket_cube, 1.2, now)
            else:
                self._start_move(self.pos_basket_cyl, 1.2, now)
                
        elif self.state == "SWINGING":
            # Arrived at basket. Wait 0.8s to let inertia settle.
            self.state = "SETTLING"
            self.timer = now + 0.8
            
        elif self.state == "SETTLING":
            if now > self.timer:
                self._set_gripper(False) # DROP!
                self.state = "PAUSE_DROP"
                self.timer = now + 0.4 # Let it fall away before moving
                
        elif self.state == "PAUSE_DROP":
            if now > self.timer:
                self.state = "RETURNING"
                # Go back home smoothly over 1.5 seconds
                self._start_move(self.pos_home, 1.5, now)
                
        elif self.state == "RETURNING":
            self.state = "HOME"

        return self.state