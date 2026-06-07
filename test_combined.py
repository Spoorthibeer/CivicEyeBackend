import os
import cv2
from ultralytics import YOLO

def is_overlapping(box1, box2):
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    if x1_1 > x2_2 or x1_2 > x2_1:
        return False
    if y1_1 > y2_2 or y1_2 > y2_1:
        return False
    return True

img_path = "latest_test.jpg"
model_std = YOLO("yolov8n.pt")
model_custom = YOLO("CivicEye_v1.pt")

results_std = model_std(img_path, conf=0.25)
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

print(f"Found {len(persons)} persons and {len(motorcycles)} motorcycles")

detected_violations = set()
for moto_box in motorcycles:
    associated_persons = 0
    for person_box in persons:
        if is_overlapping(moto_box, person_box):
            associated_persons += 1
    
    print(f"Moto associated with {associated_persons} persons")
    if associated_persons >= 3:
        detected_violations.add("Triple Riding")

results_custom = model_custom(img_path, conf=0.10, iou=0.3)
for r in results_custom:
    classes = r.boxes.cls.tolist()
    if 3 in classes or (7 in classes and 1 not in classes):
        detected_violations.add("No Helmet")
        
print("Final Violations:", ", ".join(list(detected_violations)))
