import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def analyze_geometry(image_bytes):
    try:
        # 1. Decode Image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None: return 0.5, "ERROR_DECODE"

        # 2. Advanced Preprocessing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Remove shadows using Morphology (Background Subtraction)
        dilated_bg = cv2.dilate(gray, np.ones((7,7), np.uint8))
        bg_blur = cv2.medianBlur(dilated_bg, 21)
        diff_img = 255 - cv2.absdiff(gray, bg_blur)
        norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        
        # Otsu Thresholding
        _, binary = cv2.threshold(norm_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # 3. Horizontal Smearing (Connect words)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 2)) # Tuned width
        dilated = cv2.dilate(binary, kernel, iterations=1)

        # 4. Find Contours
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_boxes = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            # Filter noise: Must be wider than 30px and taller than 8px
            if w > 30 and h > 8: 
                valid_boxes.append((y, h))

        valid_boxes.sort(key=lambda b: b[0])

        if len(valid_boxes) < 4:
            return 0.88, "HIGH RISK (No Structure)"

        # 5. Row Clustering (Merge broken lines)
        rows = []
        if valid_boxes:
            current_row_y = valid_boxes[0][0]
            current_row_count = 1
            
            for i in range(1, len(valid_boxes)):
                y, h = valid_boxes[i]
                # Merge if within 25px vertical distance
                if abs(y - current_row_y) < 25: 
                    current_row_y = (current_row_y * current_row_count + y) / (current_row_count + 1)
                    current_row_count += 1
                else:
                    rows.append(current_row_y)
                    current_row_y = y
                    current_row_count = 1
            rows.append(current_row_y)

        if len(rows) < 3: return 0.5, "INCONCLUSIVE"

        # 6. Calculate Raw Spacings
        spacings = []
        for i in range(1, len(rows)):
            dist = rows[i] - rows[i-1]
            spacings.append(dist)

        # 7. PARAGRAPH FILTER (The Critical Fix)
        # Calculate Median Spacing
        median_spacing = np.median(spacings)
        
        # Filter out gaps that are too small (noise) or too large (paragraph breaks)
        # Valid line gap is between 0.5x and 1.8x the median
        valid_spacings = [s for s in spacings if 0.5 * median_spacing < s < 1.8 * median_spacing]

        if not valid_spacings: return 0.5, "INCONCLUSIVE"

        # 8. Coefficient of Variation on CLEANED Data
        mean_s = np.mean(valid_spacings)
        std_s = np.std(valid_spacings)
        consistency = std_s / mean_s if mean_s > 0 else 1.0
        
        print(f"[ANALYSIS] Raw CV: {consistency:.3f} | Valid Lines: {len(valid_spacings)}/{len(spacings)}")

        # 9. Final Verdict (Relaxed Thresholds)
        # < 0.35 is mostly normal for webcam handwriting
        if consistency < 0.35:
            score = 0.10 + consistency
            return score, "NORMAL"
        elif consistency < 0.55:
            score = 0.40 + consistency
            return score, "MILD IRREGULARITY"
        else:
            return 0.88, "HIGH RISK"

    except Exception as e:
        print(f"Error: {e}")
        return 0.5, "ERROR_PROCESSING"

@app.post("/scan")
async def scan_handwriting(file: UploadFile = File(...)):
    if not file.content_type.startswith('image/'):
        raise HTTPException(400, detail="Invalid file type")
    
    contents = await file.read()
    score, diagnosis = analyze_geometry(contents)
    
    return {
        "status": "success",
        "diagnosis": diagnosis,
        "score": score,
        "filename": file.filename
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)