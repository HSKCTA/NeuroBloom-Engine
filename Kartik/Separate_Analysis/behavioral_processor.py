"""
behavioral_processor.py
Extracts biometric features from raw HID (Human Interface Device) logs.
"""
import numpy as np

class BehavioralProcessor:
    def __init__(self):
        pass

    def process_keystrokes(self, key_logs):
        """
        key_logs: list of (timestamp, key, event_type)
        Returns: {flight_time_var, error_rate, dwell_time_avg}
        """
        if not key_logs:
            return {"flight_time_var": 0, "error_rate": 0, "dwell_time_avg": 0}

        # Calculate Flight Time (Time between Release A and Press B)
        flight_times = []
        dwell_times = []
        errors = 0
        
        for i in range(1, len(key_logs)):
            t1, k1, evt1 = key_logs[i-1]
            t2, k2, evt2 = key_logs[i]
            
            # Simple dwell calculation (approximate for simulation)
            if evt1 == "PRESS" and evt2 == "RELEASE" and k1 == k2:
                dwell_times.append(t2 - t1)
            
            # Flight time
            flight_times.append(t2 - t1)

            if k2 == "BACKSPACE":
                errors += 1

        return {
            "flight_time_var": np.var(flight_times) if flight_times else 0,
            "dwell_time_avg": np.mean(dwell_times) if dwell_times else 0,
            "error_rate": errors / len(key_logs) if len(key_logs) > 0 else 0
        }

    def process_mouse(self, mouse_logs):
        """
        mouse_logs: list of (timestamp, x, y)
        Returns: {velocity_avg, jerk_avg, idle_ratio}
        """
        if len(mouse_logs) < 2:
            return {"velocity_avg": 0, "jerk_avg": 0, "idle_ratio": 1.0}

        velocities = []
        idle_frames = 0
        
        for i in range(1, len(mouse_logs)):
            t1, x1, y1 = mouse_logs[i-1]
            t2, x2, y2 = mouse_logs[i]
            
            dt = (t2 - t1) if (t2 - t1) > 0 else 0.001
            dist = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            vel = dist / dt
            
            if vel < 0.1: # Pixel per ms threshold
                idle_frames += 1
                
            velocities.append(vel)

        # Jerk is rate of change of acceleration (2nd derivative of velocity)
        accelerations = np.diff(velocities)
        jerks = np.diff(accelerations)

        return {
            "velocity_avg": np.mean(velocities),
            "jerk_avg": np.mean(np.abs(jerks)) if len(jerks) > 0 else 0,
            "idle_ratio": idle_frames / len(mouse_logs)
        }