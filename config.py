# ==========================================
# FACTORY CONFIGURATION
# ==========================================

# --- Speeds & Timings ---
MAIN_BELT_SPEED = 0.1
SHORT_BELT_SPEED = 0.1
SPAWNER_TARGET_SPACING = 0.5

# --- Station Logic Timers ---
LASER_COOLDOWN_SEC = 0.3
PUSH_DURATION_SEC = 1.2

# --- Robot Kinematics & Geometry ---
ROBOT_DROP_HEIGHT = 0.30
ROBOT_HOVER_CLEARANCE = 0.25
ROBOT_REACH = -0.55
ROBOT_BASE_DEG_CUBE = 120       # <--- CHECK THIS LINE
ROBOT_BASE_DEG_CYLINDER = 200    # <--- AND THIS ONE

# --- Hardware Paths ---
PATHS = {
    "camera": '/visionSensor',
    "shutter_sensor": '/proximitySensor_5',
    "spawn_point": '/Spawn_point',
    "main_belts": ['/conveyor_1', '/conveyor_2', '/conveyor_3'],
    
    "spawner_templates": [
        ('/Red_cylinder', "RED CYLINDER"),
        ('/Blue_cylinder', "BLUE CYLINDER"),
        ('/Red_cuboid', "RED CUBOID"),
        ('/Blue_cuboid', "BLUE CUBOID")
    ]
}

# --- Station Definitions ---
STATIONS = {
    "ST1": {
        "name": "Station 1",
        "pusher": '/Joint_pusher',
        "laser": '/proximitySensor_1',
        "short_belt": '/conveyor_4',
        "end_sensor": '/proximitySensor_3',
        "robot_base": '/UR5_1',
        "targets": ["red_cube", "red_cylinder"]
    },
    "ST2": {
        "name": "Station 2",
        "pusher": '/Joint_pusher_2',
        "laser": '/proximitySensor_2',
        "short_belt": '/conveyor_5',
        "end_sensor": '/proximitySensor_4',
        "robot_base": '/UR5_2',
        "targets": ["blue_cube", "blue_cylinder"]
    }
}