import cv2
import os
import math
import time
from shared import classNames, insert_image_detection, model

# ฟังก์ชันสำหรับตรวจจับวัตถุในรูปภาพ
def detect_objects(frame):
    results = model(frame)
    timestamp = time.strftime('%H:%M:%S')
    detected = False
    detections = []
    for box in results.xyxy[0]:
        conf = box[4]
        if conf >= 0.5000:  # Confidence threshold
            detected = True
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)

            conf = math.ceil((conf * 100)) / 100
            cls = int(box[5])
            class_name = classNames[cls]
            label = f'{class_name} {conf}'
            cv2.putText(frame, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)
            detections.append((class_name, conf, timestamp))

            insert_image_detection(class_name, conf, timestamp)
    return frame, detections

# ฟังก์ชันสำหรับตรวจจับวัตถุและปรับขนาดรูปภาพ
def analyze_image_with_resize(image_path):
    frame = cv2.imread(image_path)
    
    # Resize the image to 640 width while maintaining the aspect ratio
    height, width = frame.shape[:2]
    new_width = 640
    new_height = int(height * (new_width / width))
    resized_frame = cv2.resize(frame, (new_width, new_height))
    
    frame, detections = detect_objects(resized_frame)
    
    # สร้างชื่อไฟล์สำหรับภาพที่ตรวจจับแล้ว
    detected_image_path = os.path.join('static', 'detected.jpg')
    cv2.imwrite(detected_image_path, frame)
    
    # ลบภาพเดิม
    os.remove(image_path)
    
    return detected_image_path, detections

# ฟังก์ชันสำหรับตรวจจับวัตถุโดยไม่ปรับขนาดรูปภาพ
def analyze_image(image_path):
    frame = cv2.imread(image_path)
    frame, detections = detect_objects(frame)
    
    # สร้างชื่อไฟล์สำหรับภาพที่ตรวจจับแล้ว
    detected_image_path = os.path.join('static', 'detected.jpg')
    cv2.imwrite(detected_image_path, frame)
    
    # ลบภาพเดิม
    os.remove(image_path)
    
    return detected_image_path, detections