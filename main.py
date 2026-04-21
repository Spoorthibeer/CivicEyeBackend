import cv2
import pytesseract
from ultralytics import YOLO
from supabase import create_client
import time
import os

# --- 1. SETUP ---
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SUPABASE_URL = "https://xgrgygzuulmvpcgrysvl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhncmd5Z3p1dWxtdnBjZ3J5c3ZsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzUwNTM3MTIsImV4cCI6MjA5MDYyOTcxMn0.tSofeJsMQ_jjOv72wppzpiGZr9Yqo0l6BpvsxuJ5rns"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Load your custom trained model
model = YOLO("CivicEye_v1.pt") 

def get_fine_amount(violation):
    fines = {
        "No Helmet": 1035,
        "Triple Riding": 1200,
        "Wrong Route": 1100,
        "Signal Jump": 1000,
        "Clear": 0
    }
    return fines.get(violation, 0)

def download_image(file_name):
    if not os.path.exists('temp'):
        os.makedirs('temp')
    local_path = os.path.join('temp', file_name)
    try:
        res = supabase.storage.from_('evidence').download(file_name)
        with open(local_path, 'wb+') as f:
            f.write(res)
        return local_path
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None

def process_report(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return "Clear", "ERROR_IMAGE"

    # CRITICAL CHANGE: Lowering conf to 0.10 and iou to 0.3 for road captures
    results = model(image_path, conf=0.10, iou=0.3) 
    detected_violation = "Clear"
    plate_text = "NOT_FOUND"

    for r in results:
        classes = r.boxes.cls.tolist()
        
        # Mapping based on your Roboflow classes:
        # 0: green, 1: Helmet, 2: LP, 3: No Helmet, 4: number_plate, 6: red, 7: Rider
        
        # 1. TRIPLE RIDING (Class 7)
        if classes.count(7) >= 3:
            detected_violation = "Triple Riding"
        
        # 2. NO HELMET (Explicitly Class 3)
        elif 3 in classes:
            detected_violation = "No Helmet"
            
        # 3. FALLBACK: Rider present but NO Helmet detected (Class 7 found, Class 1 NOT found)
        elif 7 in classes and 1 not in classes:
            detected_violation = "No Helmet"

        # 4. SIGNAL JUMP (Class 6: red and Class 7: Rider)
        elif 6 in classes and 7 in classes:
            detected_violation = "Signal Jump"

        # 5. LICENSE PLATE OCR (Class 2 or 4)
        for box in r.boxes:
            class_id = int(box.cls[0])
            if class_id in [2, 4]: 
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Increased padding (10px) to handle angled road plates
                h, w, _ = img.shape
                pad = 10
                y1, y2 = max(0, y1-pad), min(h, y2+pad)
                x1, x2 = max(0, x1-pad), min(w, x2+pad)
                
                plate_crop = img[y1:y2, x1:x2]
                if plate_crop.size == 0: continue

                # Pre-processing for Tesseract
                gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                # Resize 3x for road-distance plates
                gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
                gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

                config = r'--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                extracted_text = pytesseract.image_to_string(gray, config=config).strip()
                
                if len(extracted_text) > 4:
                    plate_text = extracted_text.replace(" ", "")

    return detected_violation, plate_text

def start_processing():
    print("🚀 CivicEye Final Backend Running (TG Govt Optimization)...")
    print("📡 Monitoring Supabase for 'Pending' reports...")
    
    while True:
        try:
            response = supabase.table("reports").select("*").eq("status", "Pending").execute()
            reports = response.data

            for report in reports:
                print(f"🔍 Analyzing: {report['image_url']}")
                local_file = download_image(report['image_url'])
                
                if local_file:
                    violation, plate = process_report(local_file)
                    fine = get_fine_amount(violation)

                    # Update status to 'Verified' so it appears on the Police Dashboard
                    supabase.table("reports").update({
                        "ocr_plate": plate,
                        "violation_type": violation,
                        "fine_amount": fine,
                        "status": "Verified" 
                    }).eq("id", report['id']).execute()
                    
                    print(f"✅ AI Analysis Complete -> Violation: {violation} | Plate: {plate}")
                    print(f"--------------------------------------------------")
            
        except Exception as e:
            print(f"Loop error: {e}")
            
        time.sleep(5)

if __name__ == "__main__":
    start_processing()