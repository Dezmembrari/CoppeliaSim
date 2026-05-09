import csv
import time
from datetime import datetime
import os

class StatsLogger:
    def __init__(self):
        self.total_objects = 0
        self.start_time = time.time()
        self.inference_times = []
        
        # Keep the project root clean by putting CSVs in a dedicated folder
        if not os.path.exists("Reports"):
            os.makedirs("Reports")
            
        self.filename = f"Reports/sorting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Write the CSV Header row
        with open(self.filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Timestamp", 
                "Total Objects Sorted", 
                "Session Time (s)", 
                "Current Inference (ms)", 
                "Avg Inference (ms)", 
                "Prediction", 
                "Mode"
            ])

    def log_event(self, prediction, inference_ms, mode):
        """Called every time an object passes the camera."""
        self.total_objects += 1
        self.inference_times.append(inference_ms)
        
        avg_inf = sum(self.inference_times) / len(self.inference_times)
        session_time = time.time() - self.start_time
        
        # Append the new data row to the CSV
        with open(self.filename, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%H:%M:%S"), 
                self.total_objects, 
                f"{session_time:.2f}", 
                f"{inference_ms:.2f}",
                f"{avg_inf:.2f}", 
                prediction,
                mode
            ])