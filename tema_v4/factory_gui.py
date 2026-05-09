import sys
import time
import cv2
import numpy as np
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QLabel, QSlider, 
                             QPushButton, QTextEdit, QFrame)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap, QFont

# Project Imports
import config
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from vision import get_camera_state
from actuators import set_conveyor_speed
from station_manager import Station
from spawner import Spawner
from gui_state import GUIState

# --- NEW IMPORTS ---
from ml_inference import load_ai_model, ask_ai
from classic_vision import ask_classic
from stats_logger import StatsLogger

# =========================================================
# SIMULATION THREAD: Handles ZMQ Communication
# =========================================================
class SimWorker(QThread):
    vision_ready = pyqtSignal(np.ndarray)
    stats_ready = pyqtSignal(dict)
    log_ready = pyqtSignal(str)

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.logger = StatsLogger() # <-- Initialize CSV Logger

    def run(self):
        self.log_ready.emit("System: Initializing ZMQ Client...")
        client = RemoteAPIClient()
        sim = client.require('sim')
        client.setStepping(True) 

        # Setup Hardware
        st2 = Station(sim, self.state, **config.STATIONS["ST2"])
        st1 = Station(sim, self.state, **config.STATIONS["ST1"], next_queue=st2.in_queue)
        stations = [st1, st2]
        
        item_spawner = Spawner(sim, config.SPAWNER_TARGET_SPACING)
        rf_model = load_ai_model()
        
        main_belts = [sim.getObject(p) for p in config.PATHS["main_belts"]]
        shutter_sensor = sim.getObject(config.PATHS["shutter_sensor"])
        master_cam = sim.getObject(config.PATHS["camera"])

        last_speed_sent = -1.0
        shutter_last = False

        while self.state.app_open:
            curr_state = sim.getSimulationState()
            if self.state.sim_active and curr_state == sim.simulation_stopped:
                sim.startSimulation()
                self.log_ready.emit("System: Simulation Started.")
            elif not self.state.sim_active and curr_state != sim.simulation_stopped:
                sim.stopSimulation()
                self.log_ready.emit("System: Simulation Stopped.")

            if curr_state == sim.simulation_stopped:
                time.sleep(0.1) 
                continue

            frame_start = time.perf_counter()
            now = sim.getSimulationTime()

            # --- AI / CLASSIC SHUTTER LOGIC ---
            res_s = sim.readProximitySensor(shutter_sensor)
            if res_s[0] > 0 and not shutter_last:
                img, _ = get_camera_state(sim, master_cam)
                if img is not None:
                    self.vision_ready.emit(img)
                    
                    inference_start = time.perf_counter()
                    
                    # Route based on GUI Toggle
                    if self.state.use_ml_mode:
                        pred, conf = ask_ai(img, rf_model)
                        mode_str = "ML"
                    else:
                        pred, conf = ask_classic(img)
                        mode_str = "CLASSIC"
                        
                    inference_ms = (time.perf_counter() - inference_start) * 1000
                    
                    self.state.last_prediction = pred
                    self.state.last_confidence = conf
                    self.state.inference_latency_ms = inference_ms
                    
                    self.log_ready.emit(f"Vision [{mode_str}]: Detected {pred.upper()} ({conf:.1f}%) in {inference_ms:.1f}ms")
                    
                    # Log to CSV
                    self.logger.log_event(pred, inference_ms, mode_str)
                    
                    st1.in_queue.append(pred)
            shutter_last = (res_s[0] > 0)

            # Logistics & Speed Control
            force_stop = False
            for st in stations:
                if st.update(now): force_stop = True

            target_speed = 0.0 if force_stop else self.state.main_speed
            if target_speed != last_speed_sent:
                set_conveyor_speed(sim, main_belts, target_speed)
                last_speed_sent = target_speed

            # Spawner
            log_msg = item_spawner.update(now, target_speed, 
                                          self.state.auto_spawn_enabled, 
                                          self.state.spawn_request_queue,
                                          self.state.spawn_spacing)
            if log_msg: self.log_ready.emit(log_msg)

            # Send Telemetry to GUI
            latency = (time.perf_counter() - frame_start) * 1000
            self.stats_ready.emit({
                "time": f"{now:.2f}s",
                "latency": f"{latency:.2f}ms",
                "pred": f"{self.state.last_prediction} ({self.state.last_confidence:.1f}%)"
            })

            client.step()

# =========================================================
# MAIN GUI WINDOW
# =========================================================
class FactoryControlPanel(QMainWindow):
    def __init__(self):
        super().__init__()
        self.state = GUIState()
        self.setWindowTitle("UR5 Industrial Factory Command Center")
        self.resize(1100, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.init_dashboard()
        self.init_spawner_tab()
        self.init_vision()
        self.init_advanced_tab()
        self.init_pallet_tab()

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #0b0b0b; color: #00FF41; font-family: monospace;")
        self.log_output.setMaximumHeight(200)
        main_layout.addWidget(self.log_output)

        self.worker = SimWorker(self.state)
        self.worker.vision_ready.connect(self.update_camera_frame)
        self.worker.stats_ready.connect(self.update_telemetry)
        self.worker.log_ready.connect(lambda msg: self.log_output.append(msg))
        self.worker.start()

    def init_dashboard(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("START SIMULATION")
        self.btn_start.setStyleSheet("background-color: #2e7d32; color: white; padding: 15px; font-weight: bold;")
        self.btn_start.clicked.connect(self.start_sim)
        
        self.btn_stop = QPushButton("STOP SIMULATION")
        self.btn_stop.setStyleSheet("background-color: #c62828; color: white; padding: 15px; font-weight: bold;")
        self.btn_stop.clicked.connect(self.stop_sim)
        
        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

        self.lbl_time = QLabel("Sim Time: 0.00s")
        self.lbl_latency = QLabel("ZMQ Round-Trip: 0.00ms")
        self.lbl_time.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(self.lbl_time)
        layout.addWidget(self.lbl_latency)

        layout.addWidget(QLabel("\nGlobal Main Belt Speed Control:"))
        self.add_generic_slider(layout, "Main Speed", 0, 20, 
                               int(self.state.main_speed * 100), 
                               lambda v: setattr(self.state, 'main_speed', v/100.0))
        
        layout.addStretch()
        self.tabs.addTab(tab, "Dashboard")

    def init_spawner_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("--- Spacing Control ---"))
        self.lbl_spacing = QLabel(f"Object Spacing: {self.state.spawn_spacing:.2f}m")
        layout.addWidget(self.lbl_spacing)
        
        sld_spacing = QSlider(Qt.Orientation.Horizontal)
        sld_spacing.setRange(20, 200)
        sld_spacing.setValue(int(self.state.spawn_spacing * 100))
        sld_spacing.valueChanged.connect(self.on_spacing_slide)
        layout.addWidget(sld_spacing)

        layout.addSpacing(20)
        layout.addWidget(QLabel("--- Manual Production Requests ---"))
        for _, name in config.PATHS["spawner_templates"]:
            btn = QPushButton(f"Request: {name}")
            btn.clicked.connect(lambda checked, n=name: self.request_spawn(n))
            layout.addWidget(btn)

        layout.addSpacing(30)
        self.auto_toggle = QPushButton("ENABLE AUTOMATIC RANDOM SPAWNER")
        self.auto_toggle.setCheckable(True)
        self.auto_toggle.setStyleSheet("background-color: #333; color: white; padding: 15px;")
        self.auto_toggle.clicked.connect(self.toggle_auto)
        layout.addWidget(self.auto_toggle)

        layout.addStretch()
        self.tabs.addTab(tab, "Spawner Control")

    def init_vision(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # --- NEW TOGGLE BUTTON ---
        self.btn_toggle_ml = QPushButton("MODE: MACHINE LEARNING ACTIVE")
        self.btn_toggle_ml.setStyleSheet("background-color: #4a148c; color: white; padding: 15px; font-weight: bold; font-size: 14px;")
        self.btn_toggle_ml.clicked.connect(self.toggle_vision_mode)
        layout.addWidget(self.btn_toggle_ml)
        
        layout.addSpacing(10)
        
        self.cam_display = QLabel("Camera Feed Offline")
        self.cam_display.setFixedSize(512, 512)
        self.cam_display.setStyleSheet("background-color: black; border: 2px solid #555;")
        self.cam_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.cam_display)
        
        self.lbl_ai_res = QLabel("Last AI Result: (Waiting)")
        self.lbl_ai_res.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_ai_res)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Vision & AI")

    def init_advanced_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("--- Pusher Timing (Seconds) ---"))
        self.add_generic_slider(layout, "Push Duration", 5, 50, int(self.state.push_duration * 10), 
                                lambda v: setattr(self.state, 'push_duration', v/10.0))
        self.add_generic_slider(layout, "Laser Cooldown", 1, 50, int(self.state.laser_cooldown * 10), 
                                lambda v: setattr(self.state, 'laser_cooldown', v/10.0))

        layout.addWidget(QLabel("\n--- Robot Geometry (Meters) ---"))
        self.add_generic_slider(layout, "Drop Height", 10, 60, int(self.state.robot_drop_height * 100), 
                                lambda v: setattr(self.state, 'robot_drop_height', v/100.0))
        self.add_generic_slider(layout, "Hover Clearance", 5, 50, int(self.state.robot_hover_clearance * 100), 
                                lambda v: setattr(self.state, 'robot_hover_clearance', v/100.0))
        self.add_generic_slider(layout, "Arm Reach", -80, -30, int(self.state.robot_reach * 100), 
                                lambda v: setattr(self.state, 'robot_reach', v/100.0))

        layout.addWidget(QLabel("\n--- Basket Placement (Degrees) ---"))
        self.add_generic_slider(layout, "Cube Angle", 0, 360, self.state.robot_base_deg_cube, 
                                lambda v: setattr(self.state, 'robot_base_deg_cube', v))
        self.add_generic_slider(layout, "Cylinder Angle", 0, 360, self.state.robot_base_deg_cylinder, 
                                lambda v: setattr(self.state, 'robot_base_deg_cylinder', v))

        layout.addStretch()
        self.tabs.addTab(tab, "Advanced Settings")

    def init_pallet_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        layout.addWidget(QLabel("--- Pallet Grid Configuration ---"))
        self.add_generic_slider(layout, "Grid Spacing (m)", 5, 25, int(self.state.pallet_spacing * 100), 
                                lambda v: setattr(self.state, 'pallet_spacing', v/100.0))
        
        self.add_generic_slider(layout, "Grid Size (NxN)", 2, 5, self.state.pallet_grid_size, 
                                lambda v: setattr(self.state, 'pallet_grid_size', v))

        btn_reset = QPushButton("RESET PALLET COUNTERS")
        btn_reset.setStyleSheet("background-color: #555; color: white; padding: 10px;")
        btn_reset.clicked.connect(self.reset_pallets)
        layout.addWidget(btn_reset)

        layout.addStretch()
        self.tabs.addTab(tab, "Palletizing")

    def add_generic_slider(self, layout, label, min_v, max_v, curr_v, callback):
        lbl = QLabel(f"{label}: {curr_v}")
        layout.addWidget(lbl)
        sld = QSlider(Qt.Orientation.Horizontal)
        sld.setRange(min_v, max_v)
        sld.setValue(curr_v)
        sld.valueChanged.connect(lambda v: [callback(v), lbl.setText(f"{label}: {v}")])
        layout.addWidget(sld)

    def start_sim(self): self.state.sim_active = True
    def stop_sim(self): self.state.sim_active = False
    
    def toggle_auto(self):
        self.state.auto_spawn_enabled = self.auto_toggle.isChecked()
        self.auto_toggle.setStyleSheet(f"background-color: {'#1565c0' if self.state.auto_spawn_enabled else '#333'}; color: white; padding: 15px;")
        
    def on_spacing_slide(self, val):
        self.state.spawn_spacing = val / 100.0
        self.lbl_spacing.setText(f"Object Spacing: {self.state.spawn_spacing:.2f}m")
        
    def on_speed_slide(self, val): self.state.main_speed = val / 100.0
    def request_spawn(self, name): self.state.spawn_request_queue.append(name)
    def reset_pallets(self): self.log_output.append("UI: Pallet reset requested")

    # --- NEW TOGGLE HANDLER ---
    def toggle_vision_mode(self):
        self.state.use_ml_mode = not self.state.use_ml_mode
        if self.state.use_ml_mode:
            self.btn_toggle_ml.setText("MODE: MACHINE LEARNING ACTIVE")
            self.btn_toggle_ml.setStyleSheet("background-color: #4a148c; color: white; padding: 15px; font-weight: bold; font-size: 14px;")
            self.log_output.append("System: Switched to Random Forest Classifier.")
        else:
            self.btn_toggle_ml.setText("MODE: CLASSIC VISION ACTIVE")
            self.btn_toggle_ml.setStyleSheet("background-color: #e65100; color: white; padding: 15px; font-weight: bold; font-size: 14px;")
            self.log_output.append("System: Switched to OpenCV Deterministic Logic.")

    def update_telemetry(self, data):
        self.lbl_time.setText(f"Sim Time: {data['time']}")
        self.lbl_latency.setText(f"ZMQ Round-Trip: {data['latency']}")
        self.lbl_ai_res.setText(f"Last AI Result: {data['pred']}")

    def update_camera_frame(self, cv_img):
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_img.shape
        qt_img = QImage(rgb_img.data, w, h, ch * w, QImage.Format.Format_RGB888)
        self.cam_display.setPixmap(QPixmap.fromImage(qt_img).scaled(512, 512, Qt.AspectRatioMode.KeepAspectRatio))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FactoryControlPanel()
    window.show()
    sys.exit(app.exec())