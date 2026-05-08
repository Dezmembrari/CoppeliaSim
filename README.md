# UR5 Industrial AI Sorting Cell

A high-performance, synchronous robotics simulation project that integrates **CoppeliaSim** with a **Python-based Control Stack**. This project features a multi-threaded PyQt6 GUI, real-time AI classification, and an optimized ZMQ-based control architecture for UR5 robotic arms.

---

## 🚀 Project Overview

This system simulates a modern automated sorting facility where objects (Cubes and Cylinders) are classified by a centralized **Vision & AI** system and sorted into palletized grids by UR5 robotic arms.

### Key Capabilities:
* **Synchronous Simulation**: The Python control loop dictates the physics steps, ensuring deterministic behavior regardless of network lag.
* **Multi-Threaded GUI**: The UI and simulation engine run on separate threads, ensuring a responsive interface even during heavy computation.
* **Smart Spawner**: Uses an "odometer" system to maintain precise spacing between objects.
* **Live Tuning**: Real-time adjustment of robot reach, drop heights, pusher timers, and pallet grid sizes via the Advanced tabs.

---

## 📂 File Architecture

### 1. Control & GUI Layer
* **`factory_gui.py`**: The main entry point launching the PyQt6 window and the `SimWorker` thread.
* **`gui_state.py`**: A thread-safe object for sharing live-tuned variables between the GUI and simulation.
* **`config.py`**: Central repository for hardware paths and initial constants.

### 2. Simulation & Logistics Layer
* **`station_manager.py`**: Manages the conveyor, sensors, and task hand-off for individual sorting stations.
* **`spawner.py`**: Handles object creation with support for both automatic and manual GUI requests.
* **`pusher_controller.py`**: Manages the extension/retraction timing of pneumatic pushers.

### 3. Perception & Robotics Layer
* **`vision.py`**: Processes 128x128 sensor images for feature extraction.
* **`ml_inference.py`**: Classifies objects using a trained Random Forest model.
* **`robot_controller.py`**: Executes the Pick-and-Place state machine with ZMQ performance monitoring.
* **`kinematics.py`**: Custom Inverse Kinematics engine for the UR5 6-DOF geometry.
* **`palletizer.py`**: Calculates grid coordinates for organized palletizing.
* **`actuators.py`**: Cached API wrapper for high-speed conveyor control.

---

## 🛠️ Getting Fired Up (Setup Guide)

We use `uv` for high-speed Python package management.

### 1. Install `uv`
**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create the Virtual Environment
Navigate to the project directory and run:
```bash
uv venv
```

### 3. Install Requirements
```bash
uv pip install PyQt6 opencv-python numpy joblib scikit-learn coppeliasim-zmqremoteapi-client
```

---

## 🎮 Starting the Project

1. **Open CoppeliaSim** and load your `.ttt` factory scene.
2. **Run the GUI**:
   ```bash
   uv run factory_gui.py
   ```
3. **Initialize**:
    * Click **"START SIMULATION"** on the Dashboard.
    * Use **"Spawner Control"** to adjust spacing and begin production.
    * Use **"Advanced Settings"** to fine-tune robot reach and pusher durations in real-time.
    * Monitor the **Log Box** for system events and ZMQ latency stats.