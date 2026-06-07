import os
import cv2
import requests
from supabase import create_client, Client
from ultralytics import YOLO
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Get latest report
response = supabase.table("reports").select("*").order("created_at", desc=True).limit(1).execute()
if len(response.data) > 0:
    report = response.data[0]
    img_url = f"{url}/storage/v1/object/public/evidence/{report['image_url']}"
    print(f"Downloading {img_url}")
    r = requests.get(img_url)
    img_path = "latest_test.jpg"
    with open(img_path, 'wb') as f:
        f.write(r.content)
    
    model = YOLO("CivicEye_v1.pt")
    results = model(img_path, conf=0.10, iou=0.3)
    
    print("\n--- DETECTIONS ---")
    for result in results:
        for box in result.boxes:
            cls_id = int(box.cls[0])
            name = model.names[cls_id]
            conf = float(box.conf[0])
            print(f"Class: {cls_id} ({name}), Conf: {conf:.2f}")
else:
    print("No reports found")
