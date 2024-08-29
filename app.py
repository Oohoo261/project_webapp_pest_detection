import cv2
import math
import os
import sqlite3
import time
from flask import Flask, render_template, Response, request, redirect, url_for
import torch

app = Flask(__name__, template_folder="templates")

# Load YOLOv5 model
model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/runs/train/exp2/weights/best.pt')

classNames = ['Atlas-moth', 'Black-Grass-Caterpillar', 'Coconut-black-headed-caterpillar', 'Common cutworm', 'Cricket', 'Diamondback-moth',
         'Fall-Armyworm', 'Grasshopper', 'Green-weevil', 'Leaf-eating-caterpillar', 'Oriental-Mole-Cricket', 'Oriental-fruit-fly',
          'Oryctes-rhinoceros', 'Red cotton steiner', 'Rice-Bug', 'Stem-borer', 'The-Plain-Tiger', 'White-grub']

#database

def check_schema():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(detections)")
    columns = cursor.fetchall()
    conn.close()
    for column in columns:
        print(column)

def update_schema():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    
    # Check if the old table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='detections'")
    if cursor.fetchone() is None:
        print("Table 'detections' does not exist. Skipping schema update.")
        conn.close()
        return
    
    # Create a new table with the updated schema
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            confident REAL NOT NULL,
            timestamp INTEGER NOT NULL
        )
    ''')
    
    # Copy data from the old table to the new table
    cursor.execute('''
        INSERT INTO detections_new (id, name, confident, timestamp)
        SELECT id, name, confident, timestamp
        FROM detections
    ''')
    
    # Drop the old table
    cursor.execute('DROP TABLE detections')
    
    # Rename the new table to the old table's name
    cursor.execute('ALTER TABLE detections_new RENAME TO detections')
    
    conn.commit()
    conn.close()

def create_database():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        confident REAL NOT NULL,
                        timestamp INTEGER NOT NULL
                      )''')
    conn.commit()
    conn.close()

def insert_detection(name, confident, timestamp):
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    current_timestamp = time.strftime('%H:%M:%S')  # Format time as hours:minutes:seconds
    cursor.execute("INSERT INTO detections (name, confident, timestamp) VALUES (?, ?, ?)",
                   (name, confident, current_timestamp))
    conn.commit()
    conn.close()

def fetch_data_from_database():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections")
    data = cursor.fetchall()
    conn.close()
    return data

create_database()

@app.route('/data')
def data():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections")
    rows = cursor.fetchall()
    conn.close()
    return render_template('data.html', data=rows)


@app.route('/data')
def data_page():
    # หน้าแสดงข้อมูลที่ตรวจจับได้
    return render_template('data.html')

@app.route('/delete_detection', methods=['POST'])
def delete_detection():
    detection_id = request.form.get('id')
    if detection_id:
        delete_detection_by_id(detection_id)
        return redirect(url_for('data'))
    return 'Error', 400

def delete_detection_by_id(detection_id):
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections WHERE id = ?", (detection_id,))
    conn.commit()
    conn.close()

@app.route('/delete_all_detections', methods=['POST'])
def delete_all_detections():
    try:
        conn = sqlite3.connect('databasev5.db')
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detections")  # ลบข้อมูลทั้งหมดในตาราง
        conn.commit()
        conn.close()
        return redirect(url_for('data'))  # กลับไปยังหน้าข้อมูลหลังจากลบเสร็จ
    except Exception as e:
        return f"An error occurred: {e}", 500

#camera object detect

def detect_objects(frame):
    results = model(frame)
    timestamp = time.strftime('%H:%M:%S')
    detected = False
    detections = []
    for box in results.xyxy[0]:
        conf = box[4]
        if conf >= 0.25:  # Confidence threshold
            detected = True
            x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 255), 3)

            conf = math.ceil((conf * 100)) / 100
            cls = int(box[5])
            class_name = classNames[cls]
            label = f'{class_name} {conf}'
            cv2.putText(frame, label, (x1, y1 - 2), 0, 1, [255, 255, 255], thickness=1, lineType=cv2.LINE_AA)
            detections.append((class_name, conf, timestamp))

            insert_detection(class_name, conf, timestamp)  # Removed true_positive and false_positive
    return frame, detections

def generate_frames():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open video stream or file")
        return

    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            frame, _ = detect_objects(frame)  # Get only the frame, ignoring detections here
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    cap.release()


@app.route('/')
def index():
    data = fetch_data_from_database()
    return render_template('index.html', random=time.time(), detections=data)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            detections = []
            if file.filename.lower().endswith(('png', 'jpg', 'jpeg')):
                detections = analyze_image(file_path)
            elif file.filename.lower().endswith(('mp4', 'avi')):
                detections = analyze_video(file_path)
            return render_template('upload.html', file_path=file_path, detections=detections)
    return render_template('upload.html')

def analyze_image(image_path):
    frame = cv2.imread(image_path)
    frame, detections = detect_objects(frame)
    cv2.imwrite(image_path, frame)
    return detections

def analyze_video(video_path):
    cap = cv2.VideoCapture(video_path)
    detections = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame, frame_detections = detect_objects(frame)
        detections.extend(frame_detections)
    cap.release()
    return detections

#notification

@app.route('/notification_count')
def notification_count():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM detections')
    count = cursor.fetchone()[0]
    conn.close()
    return str(count)

@app.route('/notifications')
def notifications():
    notifications = fetch_notifications()
    return render_template('notifications.html', notifications=notifications)

def fetch_notifications():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, confident, timestamp FROM detections ORDER BY timestamp DESC")
    notifications = cursor.fetchall()
    conn.close()
    return notifications

@app.route('/mark_read', methods=['POST'])
def mark_read():
    notification_id = request.form.get('notification_id')
    if notification_id:
        # ไม่ลบจากฐานข้อมูล
        return 'Notification marked as read', 200
    return 'Error', 400

def mark_notification_as_read(notification_id):
    # สมมุติว่าฟังก์ชันนี้จะทำเครื่องหมายการแจ้งเตือนว่าอ่านแล้ว
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_database()  # Ensure the database and table are created first
    update_schema()    # Update the schema
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)