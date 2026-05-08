# UR5 Industrial AI Sorting Cell

A high-performance, synchronous robotics simulation project that integrates **CoppeliaSim** with a **Python-based Control Stack**. This project features a multi-threaded PyQt6 GUI, real-time AI classification, and an optimized ZMQ-based control architecture for UR5 robotic arms.

---

## 🚀 Detailed Project Description

This system simulates a modern automated sorting facility. Objects (Cubes and Cylinders of various colors) are spawned onto a main conveyor belt. Using a centralized **Vision & AI** system, the factory identifies these objects and orchestrates a series of "Stations" to sort them into specific palletized grids.

### Key Capabilities:
* **Synchronous Simulation**: The Python control loop dictates the physics steps, ensuring perfectly deterministic behavior regardless of network lag.
* **Multi-Threaded GUI**: Operates on a dual-track architecture where the simulation engine and the user interface run in parallel, preventing UI freezing during heavy API calls.
* **Motion-Aware Spawning**: A smart spawner that uses an "odometer" system to ensure objects never overlap on the belt.
* **Optimized ZMQ Throughput**: Implements hardware-call caching and state-change monitoring to minimize redundant network traffic.

---

## 📂 File Architecture & Responsibilities

The project is divided into four logical layers to ensure modularity and ease of maintenance.

### 1. Control & GUI Layer
* **`factory_gui.py`**: The main entry point. It launches the PyQt6 window and manages the simulation worker thread that communicates with CoppeliaSim.
* **`gui_state.py`**: A thread-safe "shared memory" object that allows the GUI to send commands (like speed and spacing changes) to the simulation thread.
* **`config.py`**: The central control panel. Contains all hardware paths, logic timers, and robot spatial coordinates.

### 2. Simulation & Logistics Layer
* **`station_manager.py`**: The brain of each sorting cell. It coordinates the conveyor belts and object detection lasers, and hands off tasks to the robots.
* **`spawner.py`**: Manages the creation of objects. Supports both random automatic spawning and specific manual requests from the GUI, respecting safe distance intervals.
* **`pusher_controller.py`**: Encapsulates the mechanical timing and states (Extension/Retraction/Cooldown) of the pneumatic pushers.

### 3. Perception Layer
* **`vision.py`**: Handles OpenCV image processing. It captures 128x128 sensor frames and extracts geometric fingerprints for classification.
* **`ml_inference.py`**: The AI "Brain." Loads the pre-trained model to classify objects based on their vision fingerprints.

### 4. Robotics & Actuation Layer
* **`robot_controller.py`**: Manages the UR5 state machine (Pick, Swing, Plunge, Drop). It includes performance monitoring to track ZMQ overhead.
* **`kinematics.py`**: A custom Inverse Kinematics engine specifically tuned for the UR5's 6-axis geometry.
* **`palletizer.py`**: Calculates the precise 3D grid offsets for dropping items into baskets in organized rows.
* **`actuators.py`**: A performance-optimized wrapper for CoppeliaSim hardware commands. It automatically detects and caches the fastest API method for each conveyor.

---

## 🛠️ Getting Fired Up (Setup Guide)

We use `uv` for extremely fast Python package management.

### 1. Install `uv`
If you don't have `uv` installed, run the appropriate command for your OS:

**Windows (PowerShell):**
```powershell
powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"

macOS/Linux:
```Bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

2. Create the Virtual Environment

Navigate to the project directory and create a fresh environment:
```Bash
uv venv

3. Install Requirements

Install the necessary robotics and GUI libraries:
```Bash
uv pip install PyQt6 opencv-python numpy joblib scikit-learn coppeliasim-zmqremoteapi-client

🎮 Starting the Project

Follow these steps in order to start the system for the first time:

    Open CoppeliaSim: Launch the CoppeliaSim application.

    Load the Scene: Open your .ttt factory scene file.

    Ensure ZMQ is Active: CoppeliaSim usually starts the ZMQ remote API server automatically on port 23000.

    Run the GUI:
    ```Bash
    uv run factory_gui.py

    Initialize:

        Once the window opens, click the "START SIMULATION" button on the Dashboard.

        Navigate to the "Spawner Control" tab to begin placing objects on the line.

        Monitor the "Log Box" at the bottom for real-time system events.