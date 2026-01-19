import zmq
import json
import asyncio
import base64
import subprocess
import random
import cv2 
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

app = FastAPI()

# --- DEMO CONFIGURATION ---
FORCE_BAD_RESULT = False 

AES_KEY = b"01234567890123456789012345678901"
AES_IV  = b"0123456789012345"

# --- OPENCV HANDWRITING ANALYSIS (Same as before) ---
def analyze_handwriting_heuristic(image_data_b64=None):
    if FORCE_BAD_RESULT: return 0.88, "HIGH RISK"
    
    if image_data_b64 is None or len(image_data_b64) < 100: return 0.15, "NORMAL"

    try:
        img_bytes = base64.b64decode(image_data_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: return 0.5, "ERROR"

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 15)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
        dilated = cv2.dilate(binary, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        line_contours = [c for c in contours if cv2.boundingRect(c)[2] > 50]
        line_contours.sort(key=lambda c: cv2.boundingRect(c)[1])

        if len(line_contours) < 3: return 0.85, "HIGH RISK (No Structure)"

        spacings = []
        prev_y = cv2.boundingRect(line_contours[0])[1]
        for cnt in line_contours[1:]:
            y = cv2.boundingRect(cnt)[1]
            dist = y - prev_y
            if dist > 10: spacings.append(dist)
            prev_y = y

        if not spacings: return 0.5, "INCONCLUSIVE"
        mean_s = np.mean(spacings)
        consistency = np.std(spacings) / mean_s if mean_s > 0 else 1.0

        if consistency < 0.25: return 0.12 + consistency, "NORMAL"
        elif consistency < 0.40: return 0.45 + consistency, "MILD IRREGULARITY"
        else: return 0.88, "HIGH RISK"

    except Exception as e:
        print(f"[OCR ERROR] {e}")
        return 0.5, "ERROR"

def decrypt_payload(b64_str):
    try:
        ct = base64.b64decode(b64_str)
        cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(AES_IV), backend=default_backend())
        decryptor = cipher.decryptor()
        pt = decryptor.update(ct) + decryptor.finalize()
        return pt.decode('utf-8', errors='ignore').strip().replace('\x00', '').replace('\x10', '')
    except:
        return None

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[WEB] Frontend Connected!")
    context = zmq.Context(); socket = context.socket(zmq.SUB)
    socket.connect("tcp://127.0.0.1:5555"); socket.setsockopt_string(zmq.SUBSCRIBE, "EEG_SECURE")

    try:
        while True:
            # CHECK FRONTEND COMMANDS
            try:
                command = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                if command.startswith("SCAN_HANDWRITING"):
                    img_data = None
                    if ":" in command: _, img_data = command.split(":", 1)
                    risk, diag = analyze_handwriting_heuristic(img_data)
                    await websocket.send_json({"type": "DYSGRAPHIA_RESULT", "score": risk, "diagnosis": diag})
            except asyncio.TimeoutError: pass 

            # CHECK ZMQ STREAM
            if socket.poll(timeout=10): 
                msg = socket.recv_string()
                json_str = decrypt_payload(msg.split(" ")[1])
                
                if json_str:
                    try:
                        start = json_str.find('{'); end = json_str.rfind('}')
                        if start != -1 and end != -1: data = json.loads(json_str[start:end+1])
                        else: continue
                    except: continue
                    
                    # 1. ACADEMIC METRICS CALCULATION
                    eeg = data.get('eeg_power', {})
                    theta = eeg.get('theta', 1); beta = eeg.get('low_beta', 1)
                    gamma = (eeg.get('low_gamma',0) + eeg.get('mid_gamma',0)) / 2
                    alpha = (eeg.get('low_alpha',1) + eeg.get('high_alpha',1)) / 2
                    h_beta = eeg.get('high_beta', 0)

                    # A. ADHD: Theta/Beta Ratio
                    tbr = theta / beta if beta > 0 else 0
                    
                    # B. DYSCALCULIA: Cognitive Load
                    cog_load = gamma / theta if theta > 0 else 0
                    # stress_idx removed

                    # 2. FUSION DIAGNOSIS
                    vision = data.get('vision', {})
                    yaw = abs(vision.get('yaw', 0))
                    
                    diagnosis = "FOCUSED"
                    # If TBR is high (ADHD) or Yaw is high (Distracted)
                    if tbr > 3.5 or yaw > 80: diagnosis = "DISTRACTED"
                    # High Stress condition removed

                    data['diagnosis'] = diagnosis
                    data['metrics'] = {
                        "tbr": round(tbr, 2),
                        "cog_load": round(cog_load, 2),
                        "stress_index": 0.0, # Removed
                        "hyperactivity": round(vision.get('hyperactivity_index', 0), 2),
                        "focus_ratio": round(vision.get('focus_ratio', 0) * 100, 1),
                        "blink_count": vision.get('blink_count', 0)
                    }
                    
                    await websocket.send_json(data)
            await asyncio.sleep(0.01)
    except Exception as e: print(e)
    finally: socket.close()