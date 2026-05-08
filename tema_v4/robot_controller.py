import math
import time
from kinematics import KinematicsEngine
from palletizer import Palletizer
import config

class UR5Robot:
    def __init__(self, sim, base_path, state, name="Robot"):
        self.sim = sim
        self.gui_state = state  # Renamed to gui_state to avoid collision
        self.name = name
        
        self.kin = KinematicsEngine(d1=0.089, a2=0.425, a3=0.392, elbow_config=-1)
        self.plt = Palletizer(spacing_cm=10.0, grid_size=3)
        
        self.pickup_anchor = self._deg2rad([0, 0, -67, -23, 90, 0])
        self.orient_const = sum(self.pickup_anchor[1:4])
        
        # Initial Poses
        self.pick_reach, self.pick_height = self.kin.forward(self.pickup_anchor[1], self.pickup_anchor[2])
        res = self.kin.inverse(self.pick_reach, self.pick_height + 0.10, self.orient_const)
        self.pos_hover = [0, res[0], res[1], res[2], math.radians(90), 0]
        self.pos_home = self.pos_hover

        # Hardware Handles
        self.joints = [self.sim.getObject(f"{base_path}/joint", {"index": i}) for i in range(6)]
        self.tip = self.sim.getObject(f"{base_path}/suctionPad")
        self.sim.setObjectInt32Param(self.tip, self.sim.shapeintparam_respondable, 0)
        
        # --- CRITICAL: Initialize these attributes ---
        self.state, self.timer = "HOME", 0  # Logic State
        self.avg_update_ms = 0             # Performance tracking
        self.update_count = 0              # Performance tracking
        
        self.drop_hover_pose = None
        self.drop_low_pose = None
        self.held_object_handle = None 
        self.is_moving, self.move_start_time, self.move_duration = False, 0, 1.0
        self.start_angles, self.target_angles = [0]*6, [0]*6

        # Move to home
        for joint, angle in zip(self.joints, self.pos_home):
            self.sim.setJointTargetPosition(joint, angle)

    def _deg2rad(self, deg_list): return [math.radians(d) for d in deg_list]

    def _get_drop_poses(self, shape_name):
        """Calculates poses using live values from gui_state."""
        key = "cube" if "cube" in shape_name.lower() else "cylinder"
        
        # Update palletizer live
        self.plt.spacing = self.gui_state.pallet_spacing
        self.plt.grid_size = self.gui_state.pallet_grid_size
        dr, dl = self.plt.get_grid_offsets(key)
        
        # Use live GUI geometry
        base_deg = self.gui_state.robot_base_deg_cube if key == "cube" else self.gui_state.robot_base_deg_cylinder
        reach = self.gui_state.robot_reach
        height = self.gui_state.robot_drop_height
        clearance = self.gui_state.robot_hover_clearance

        target_reach = reach + dr
        base_nudge_rad = dl / abs(reach) if reach != 0 else 0
        target_base_rad = math.radians(base_deg) + base_nudge_rad
        
        res_high = self.kin.inverse(target_reach, height + clearance, self.orient_const)
        res_low = self.kin.inverse(target_reach, height, self.orient_const)
        
        if res_high is None or res_low is None: 
            return self.pos_home, self.pos_home
            
        pose_high = [target_base_rad, res_high[0], res_high[1], res_high[2], math.radians(90), 0]
        pose_low  = [target_base_rad, res_low[0],  res_low[1],  res_low[2],  math.radians(90), 0]
        
        return pose_high, pose_low

    def _start_move(self, target_angles, duration_sec, now):
        self.start_angles = [self.sim.getJointPosition(j) for j in self.joints]
        self.target_angles = list(target_angles)
        for i in range(6):
            diff = (self.target_angles[i] - self.start_angles[i] + math.pi) % (2 * math.pi) - math.pi
            self.target_angles[i] = self.start_angles[i] + diff
        self.move_start_time, self.move_duration, self.is_moving = now, duration_sec, True

    def _update_movement(self, now):
        if not self.is_moving: return True
        start_t = time.perf_counter()
        
        t = max(0, min(1.0, (now - self.move_start_time) / self.move_duration))
        if t >= 1.0: self.is_moving = False
        
        ease_t = 0.5 * (1 - math.cos(math.pi * t))
        target_angles = []
        for i in range(6):
            angle = self.start_angles[i] + (self.target_angles[i] - self.start_angles[i]) * ease_t
            target_angles.append(angle)
            self.sim.setJointTargetPosition(self.joints[i], angle)
        
        # Stats update
        ms = (time.perf_counter() - start_t) * 1000
        self.avg_update_ms = (self.avg_update_ms * self.update_count + ms) / (self.update_count + 1)
        self.update_count += 1
        return not self.is_moving

    def _set_gripper(self, active):
        if not self.held_object_handle: return
        self.sim.setObjectInt32Param(self.held_object_handle, self.sim.shapeintparam_respondable, 0 if active else 1)
        self.sim.setObjectInt32Param(self.held_object_handle, self.sim.shapeintparam_static, 1 if active else 0)
        self.sim.setObjectParent(self.held_object_handle, self.tip if active else -1, True)
        if not active:
            self.sim.resetDynamicObject(self.held_object_handle)
            self.held_object_handle = None

    def start_sort(self, shape_name, object_handle, now):
        self.held_object_handle = object_handle 
        self.drop_hover_pose, self.drop_low_pose = self._get_drop_poses(shape_name)
        self.state = "TO_PICKUP"
        self._start_move(self.pickup_anchor, 0.8, now)

    def update(self, now):
        if not self._update_movement(now): return self.state
        
        if self.state == "TO_PICKUP":
            self.state, self.timer = "PAUSE_GRAB", now + 0.4
        elif self.state == "PAUSE_GRAB":
            if now > self.timer:
                self._set_gripper(True)
                self.state = "LIFTING"
                self._start_move(self.pos_hover, 0.8, now)
        elif self.state == "LIFTING":
            self.state = "SWINGING_HIGH"
            self._start_move(self.drop_hover_pose, 1.2, now)
        elif self.state == "SWINGING_HIGH":
            self.state, self.timer = "PAUSE_HOVER", now + 0.5
        elif self.state == "PAUSE_HOVER":
            if now > self.timer:
                self.state = "PLUNGING"
                self._start_move(self.drop_low_pose, 0.8, now)
        elif self.state == "PLUNGING":
            self.state, self.timer = "SETTLING", now + 1.0
        elif self.state == "SETTLING":
            if now > self.timer:
                self._set_gripper(False)
                self.state, self.timer = "PAUSE_DROP", now + 0.5
        elif self.state == "PAUSE_DROP":
            if now > self.timer:
                self.state = "LIFTING_CLEAR"
                self._start_move(self.drop_hover_pose, 0.8, now)
        elif self.state == "LIFTING_CLEAR":
            self.state = "RETURNING"
            self._start_move(self.pos_home, 1.0, now)
        elif self.state == "RETURNING":
            self.state = "HOME"
            
        return self.state