# detect.py

import cv2
import math
import time
from shared import classNames, insert_detection, model

def detect_objects(frame, camera_index=0):
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
            detections.append((class_name, conf, timestamp, camera_index))

            insert_detection(class_name, conf, timestamp, camera_index)  # Include camera_index
    return frame, detections

def generate_frames(camera_index=0):
    cap = cv2.VideoCapture(camera_index)  # Use the selected camera_index
    if not cap.isOpened():
        print("Error: Could not open video stream or file")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            frame, _ = detect_objects(frame, camera_index)  # Pass the camera_index
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()

