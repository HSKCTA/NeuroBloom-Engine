"""
main.py
HYBRID ENGINE: Real Computer Vision + Synthetic EEG/Behavior.
Orchestrates the Tier 1 Diagnostic Pipeline with Active Webcam Support.
"""
import json
import time
import random
import numpy as np
import cv2  # OpenCV

from signal_generator import EEGSimulator
from behavioral_processor import BehavioralProcessor
from metrics_engine import MetricsEngine

# --- ROBUST GAZE TRACKER ---
def get_gaze_ratio(eye_roi):
    """Calculates horizontal gaze direction from Eye ROI."""
    try:
        # 1. Image Processing
        # Convert to Gray
        gray_eye = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY)
        
        # CRITICAL FIX: Crop the top 30% to remove eyebrows
        h, w = gray_eye.shape
        gray_eye = gray_eye[int(h*0.3):, :] 
        
        # Histogram equalization improves contrast for pupil detection
        gray_eye = cv2.equalizeHist(gray_eye) 
        
        # 2. Find Darkest Point (Pupil)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(gray_eye)
        
        # 3. VISUAL DEBUG: Draw the detected pupil on the main frame
        # We need to adjust coordinates back to the uncropped ROI
        pupil_x = min_loc[0]
        pupil_y = min_loc[1] + int(h*0.3)
        cv2.circle(eye_roi, (pupil_x, pupil_y), 4, (0, 0, 255), -1) # Red Dot
        
        # 4. Calculate Ratio (0.0=Left, 0.5=Center, 1.0=Right)
        ratio = pupil_x / w
        return ratio
    except Exception as e:
        return 0.5

class MockCamera:
    def __init__(self):
        self.frame_count = 0
        
    def isOpened(self):
        return True
        
    def release(self):
        pass
        
    def read(self):
        self.frame_count += 1
        # Generate a synthetic frame (noise + text)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        # Add some moving noise
        noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Add a moving circle to simulate activity
        cx = 320 + int(100 * np.sin(self.frame_count * 0.1))
        cy = 240 + int(50 * np.cos(self.frame_count * 0.1))
        cv2.circle(frame, (cx, cy), 30, (0, 255, 255), -1)
        
        cv2.putText(frame, "MOCK CAMERA MODE", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        return True, frame

def run_hybrid_session():
    print("[SYSTEM] Starting NeuroBloom Hybrid Engine (Camera ON)...")
    
    # 1. HARDWARE SETUP
    cap = cv2.VideoCapture(0) # Open Default Webcam
    
    # Load Standard Haar Cascades
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
    
    if not cap.isOpened():
        print("[ERROR] Could not open webcam. Switching to Mock Camera.")
        cap = MockCamera()

    # 2. MODULE INITIALIZATION
    eeg_sim = EEGSimulator()
    behavior_proc = BehavioralProcessor()
    
    # State Tracking
    blink_counter = 0
    eyes_closed_frames = 0
    
    print("[READY] Press 'q' to stop the session.")

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # --- A. VISION PIPELINE (Real Data) ---
        vision_metrics = {
            "yaw_velocity": 0,
            "gaze_deviation": 0, 
            "blink_count": blink_counter
        }
        
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        for (x, y, w, h) in faces:
            # Draw Face Box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # 1. Calculate Head Yaw (Offset from center)
            frame_center = frame.shape[1] / 2
            face_center = x + (w / 2)
            yaw_raw = (face_center - frame_center) / (frame.shape[1] / 2) 
            vision_metrics['yaw_velocity'] = abs(yaw_raw) * 100 

            # 2. Eye Tracking
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 5)
            
            # Blink Logic
            if len(eyes) == 0:
                eyes_closed_frames += 1
            else:
                if eyes_closed_frames > 3: 
                    blink_counter += 1
                    cv2.putText(frame, "BLINK", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                eyes_closed_frames = 0

            # Gaze Logic
            gaze_offsets = []
            for (ex, ey, ew, eh) in eyes:
                # Filter lower half of face (mouths often detected as eyes)
                if ey > h / 2: continue 
                
                # Extract Color ROI for drawing
                eye_roi = roi_color[ey:ey+eh, ex:ex+ew]
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (255, 0, 0), 1)
                
                ratio = get_gaze_ratio(eye_roi)
                
                # deviation from center (0.5)
                gaze_offsets.append(abs(ratio - 0.5))
            
            if gaze_offsets:
                vision_metrics['gaze_deviation'] = np.mean(gaze_offsets) * 2 # Normalize 0-1

        # --- B. BEHAVIORAL SIMULATION ---
        mock_mouse_data = []
        is_hyperactive = vision_metrics['yaw_velocity'] > 20
        jitter_factor = 20 if is_hyperactive else 1
        mock_mouse_data.append((time.time(), 500, 500)) 
        mock_mouse_data.append((time.time()+0.1, 500+jitter_factor, 500+jitter_factor))
        mouse_feats = behavior_proc.process_mouse(mock_mouse_data)
        
        # Simulate Keystrokes (Mocked) to fix KeyError
        mock_key_logs = []
        mock_key_logs.append((time.time(), "A", "PRESS"))
        mock_key_logs.append((time.time()+0.1, "A", "RELEASE"))
        key_feats = behavior_proc.process_keystrokes(mock_key_logs)
        
        # Merge features
        behavior_feats = {**mouse_feats, **key_feats}
        
        # --- C. PHYSICS ENGINE (Simulated EEG) ---
        sim_state = "FOCUSED"
        
        # THRESHOLD RELAXED TO 0.5 (Was 0.3)
        if vision_metrics['gaze_deviation'] > 0.5:
            sim_state = "DISTRACTED" 
        
        # HEAD OFFSET THRESHOLD (Only triggers if you move far left/right)
        if vision_metrics['yaw_velocity'] > 40:
            sim_state = "STRESSED"   
            
        eeg_epoch = eeg_sim.generate_epoch(
            state=sim_state,
            behavior_modifiers={
                "mouse_jerk": behavior_feats['jerk_avg'],
                "blink_spike": 1 if eyes_closed_frames > 2 else 0
            }
        )
        
        # --- D. METRICS & OUTPUT ---
        report = MetricsEngine.compute_all(eeg_epoch, behavior_feats, vision_metrics)
        
        # Display Stats on Screen
        color = (0, 255, 0) if sim_state == "FOCUSED" else (0, 0, 255)
        status_text = f"STATE: {sim_state} | ATTENTION: {report['focus_ratio']*100:.0f}%"
        cv2.putText(frame, status_text, (20, frame.shape[0] - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.imshow('NeuroBloom Hybrid Engine', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    
    # Print Final Report
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run_hybrid_session()
    