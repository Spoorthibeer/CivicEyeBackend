import os
import cv2
import requests
from supabase import create_client, Client
from ultralytics import YOLO
from dotenv import load_dotenv

load_dotenv()

model = YOLO("CivicEye_v1.pt")
img_path = "latest_test.jpg"

# Try with different NMS overlap thresholds
print("\n--- DETECTIONS with IOU=0.5 ---")
results = model(img_path, conf=0.10, iou=0.5)
for result in results:
    for box in result.boxes:
        cls_id = int(box.cls[0])
        print(f"Class: {cls_id} ({model.names[cls_id]}), Conf: {float(box.conf[0]):.2f}")

print("\n--- DETECTIONS with IOU=0.8 ---")
results = model(img_path, conf=0.10, iou=0.8)
for result in results:
    for box in result.boxes:
        cls_id = int(box.cls[0])
        print(f"Class: {cls_id} ({model.names[cls_id]}), Conf: {float(box.conf[0]):.2f}")
