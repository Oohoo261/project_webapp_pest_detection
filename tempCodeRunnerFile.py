import cv2
import os
import sqlite3
import time
from flask import Flask, render_template, Response, request, redirect, url_for
from image_detect import analyze_image, analyze_image_with_resize
from detect import generate_frames
from shared import create_database, update_schema, fetch_data_from_database

app = Flask(__name__, template_folder="templates")


#data.html

@app.route('/data')
def data():
    conn = sqlite3.connect('databasev5.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections")
    rows = cursor.fetchall()
    conn.close()
    return render_template('data.html', data=rows)

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

#index.html

@app.route('/')
def index():
    data = fetch_data_from_database()
    return render_template('index.html', random=time.time(), detections=data)

@app.route('/video_feed')
def video_feed():
    camera_index = int(request.args.get('camera_index', 0))  # รับ camera_index จาก query parameter
    return Response(generate_frames(camera_index), mimetype='multipart/x-mixed-replace; boundary=frame')


#upload.html

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        resize_option = request.form.get('resize')  # ดึงค่าจากฟอร์มเพื่อดูว่าผู้ใช้เลือกปรับขนาดภาพหรือไม่
        if file:
            file_path = os.path.join('uploads', file.filename)
            file.save(file_path)
            
            # ตรวจจับและบันทึกภาพที่ตรวจจับแล้ว
            if resize_option == 'yes':
                detected_file_path, detections = analyze_image_with_resize(file_path)
            else:
                detected_file_path, detections = analyze_image(file_path)
            
            return render_template('upload.html', file_path='detected.jpg', detections=detections)
    return render_template('upload.html')


#notification.html

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