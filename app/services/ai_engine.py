import cv2
import pytesseract
from ultralytics import YOLO
import os

# HARDCODED PATH: Direct link to the executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Load the custom model for OCR, Helmet, and Signal Jump
MODEL_PATH = os.path.join(os.getcwd(), "CivicEye_v1.pt")
model_custom = YOLO(MODEL_PATH)

# Load the standard YOLOv8 model for counting persons (will download automatically on first run)
model_std = YOLO("yolov8n.pt")

class AIEngine:
    @staticmethod
    def is_overlapping(box1, box2):
        """Check if two bounding boxes [x1, y1, x2, y2] overlap."""
        x1_1, y1_1, x2_1, y2_1 = box1
        x1_2, y1_2, x2_2, y2_2 = box2
        
        # If one rectangle is on left side of other
        if x1_1 > x2_2 or x1_2 > x2_1:
            return False
        # If one rectangle is above other
        if y1_1 > y2_2 or y1_2 > y2_1:
            return False
        return True

    @staticmethod
    def process_image(image_path: str):
        img = cv2.imread(image_path)
        if img is None:
            return "Clear", "NOT_FOUND"

        detected_violations = set()
        plate_text = "NOT_FOUND"

        # ==========================================
        # 1. Standard YOLOv8 for Triple Riding
        # ==========================================
        # Standard model accurately separates 'person' (0) and 'motorcycle' (3)
        results_std = model_std(image_path, conf=0.25)
        persons = []
        motorcycles = []
        
        for r in results_std:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                coords = box.xyxy[0].tolist()
                if cls_id == 0: # person
                    persons.append(coords)
                elif cls_id == 3: # motorcycle
                    motorcycles.append(coords)
        
        # Count persons whose bounding boxes overlap with the motorcycle
        for moto_box in motorcycles:
            associated_persons = 0
            for person_box in persons:
                if AIEngine.is_overlapping(moto_box, person_box):
                    associated_persons += 1
            
            if associated_persons >= 3:
                detected_violations.add("Triple Riding")
                break # Found at least one motorcycle with 3+ people

        # ==========================================
        # 2. Custom Model for No Helmet & OCR
        # ==========================================
        results_custom = model_custom(image_path, conf=0.10, iou=0.3)

        for r in results_custom:
            classes = r.boxes.cls.tolist()
            
            # Restore the original logic that successfully triggered No Helmet
            # (In the custom model, detecting a Rider (3) triggered No Helmet)
            if 3 in classes or (7 in classes and 1 not in classes) or 2 in classes:
                detected_violations.add("No Helmet")
                
            if 6 in classes and 7 in classes:
                detected_violations.add("Signal Jump")

            # OCR Logic for License Plates
            # The custom model classes for plates are 1 (LP) and 5 (number_plate)
            for box in r.boxes:
                class_id = int(box.cls[0])
                if class_id in [1, 5]: 
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    
                    h, w, _ = img.shape
                    pad = 10
                    crop = img[max(0, y1-pad):min(h, y2+pad), max(0, x1-pad):min(w, x2+pad)]
                    
                    if crop.size > 0:
                        try:
                            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                            gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                            
                            config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                            raw_text = pytesseract.image_to_string(gray, config=config)
                            current_text = raw_text.strip().replace(" ", "")
                            if current_text:
                                plate_text = current_text
                        except Exception as ocr_error:
                            print(f"⚠️ OCR Error: {ocr_error}")
                            if plate_text == "NOT_FOUND":
                                plate_text = "ERROR_READING"

        # Ensure consistent string creation
        final_violations = sorted(list(detected_violations))
        final_violation_string = ", ".join(final_violations) if final_violations else "Clear"

        return final_violation_string, plate_text