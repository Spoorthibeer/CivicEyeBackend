import os
from ultralytics import YOLO

img_path = "latest_test.jpg"

print("\n--- DETECTIONS with YOLOv8n (Standard) ---")
model = YOLO("yolov8n.pt")  # Will download automatically
results = model(img_path)
for result in results:
    for box in result.boxes:
        cls_id = int(box.cls[0])
        print(f"Class: {cls_id} ({model.names[cls_id]}), Conf: {float(box.conf[0]):.2f}")
