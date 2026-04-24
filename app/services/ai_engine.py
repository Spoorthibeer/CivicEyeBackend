import cv2
import pytesseract
from ultralytics import YOLO
import os

# HARDCODED PATH: Direct link to the executable
# Using 'r' before the string handles the backslashes correctly in Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the model (Update this path if your model is elsewhere)
# Using a relative path is usually safer for local projects
# We use the exact name from your screenshot
MODEL_PATH = os.path.join(os.getcwd(), "CivicEye_v1.pt")
model = YOLO(MODEL_PATH)

class AIEngine:
    @staticmethod
    def process_image(image_path: str):
        """
        Analyzes an image for traffic violations and extracts the number plate.
        """
        img = cv2.imread(image_path)
        if img is None:
            return "Clear", "NOT_FOUND"

        # Run detection
        results = model(image_path, conf=0.10, iou=0.3)
        detected_violation = "Clear"
        plate_text = "NOT_FOUND"

        for r in results:
            classes = r.boxes.cls.tolist()
            
            # 1. Violation Logic
            if classes.count(7) >= 3:
                detected_violation = "Triple Riding"
            elif 3 in classes:
                detected_violation = "No Helmet"
            elif 7 in classes and 1 not in classes:
                detected_violation = "No Helmet"
            elif 6 in classes and 7 in classes:
                detected_violation = "Signal Jump"

            # 2. OCR Logic for License Plates
            for box in r.boxes:
                class_id = int(box.cls[0])
                if class_id in [2, 4]: # LP or number_plate
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    h, w, _ = img.shape
                    pad = 10
                    crop = img[max(0, y1-pad):min(h, y2+pad), max(0, x1-pad):min(w, x2+pad)]
                    
                    if crop.size > 0:
                        try:
                            # Pre-process for Tesseract
                            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                            gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                            
                            config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                            raw_text = pytesseract.image_to_string(gray, config=config)
                            plate_text = raw_text.strip().replace(" ", "")
                        except Exception as ocr_error:
                            # If OCR fails, we don't want the whole backend to crash
                            print(f"⚠️ OCR Error: {ocr_error}")
                            plate_text = "ERROR_READING"

        return detected_violation, plate_text