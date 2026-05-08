# CoppeliaSim

Latest version in /tema_v4/

to setup with uv venv: uv pip install -r requirements.txt

running the facotry sim --> uv run main.py
running the object algo --> uv run spawner.py

## 📂 File Structure

* `main.py`: The central conductor. Connects to the sim, handles the AI camera, and updates all sorting stations.
* `station_manager.py`: Contains the `Station` class. Handles the state-machine logic for individual lasers, pushers, and short belts.
* `spawner.py`: The production line feeder. Tracks belt movement and drops fresh objects at exactly 1.0m intervals.
* `actuators.py`: *(Custom)* Contains helper functions for motor speeds and pusher joints.
* `vision_ml.py`: *(Custom)* Contains the AI model loading and inference logic.

---

## 🛠️ Prerequisites & Installation

1. **CoppeliaSim:** Version 4.3+ (ZMQ Remote API required).
2. **Python Dependencies:**
   ```bash
  pip install uv #if not installed already

  For starting up the env:

   ```bash
   uv venv
   uv pip install requirements.txt
   uv run main.py
   uv run spawner.py
