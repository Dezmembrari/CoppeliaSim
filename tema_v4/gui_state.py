import config

class GUIState:
    def __init__(self):
        # Simulation lifecycle
        self.app_open = True        
        self.sim_active = False     
        self.main_speed = config.MAIN_BELT_SPEED
        
        # --- Advanced Logic Timers ---
        self.laser_cooldown = config.LASER_COOLDOWN_SEC
        self.push_duration = config.PUSH_DURATION_SEC
        
        # --- Robot Kinematics & Geometry ---
        self.robot_drop_height = config.ROBOT_DROP_HEIGHT
        self.robot_hover_clearance = config.ROBOT_HOVER_CLEARANCE
        self.robot_reach = config.ROBOT_REACH
        self.robot_base_deg_cube = config.ROBOT_BASE_DEG_CUBE
        self.robot_base_deg_cylinder = config.ROBOT_BASE_DEG_CYLINDER
        
        # --- Palletizing Logic ---
        self.pallet_spacing = 0.10  # 10cm default
        self.pallet_grid_size = 3
        
        # --- Vision Mode Selection (NEW) ---
        self.use_ml_mode = True  # True = Machine Learning, False = Classic OpenCV Way
        
        # Spawner & Telemetry
        self.auto_spawn_enabled = False
        self.spawn_request_queue = [] 
        self.spawn_spacing = config.SPAWNER_TARGET_SPACING
        self.last_prediction = "None"
        self.last_confidence = 0.0
        self.sim_time = 0.0
        self.loop_latency = 0.0
        
        # --- CSV Logging Telemetry (NEW) ---
        self.total_objects_sorted = 0
        self.inference_latency_ms = 0.0