import os
import sqlite3
import time
from flask import Flask, jsonify, render_template, Response, request, redirect, url_for
from image_detect import analyze_image, analyze_image_with_resize
from detect import generate_frames
from shared import create_database, update_schema, fetch_data_from_database, update_pest_schema, create_pest_database, create_image_database, DATABASE_PATH

app = Flask(__name__, template_folder="templates")

#data.html

@app.route('/data')
def data():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    query = '''
        SELECT detections.id, pests.name_thai, detections.name, detections.confident, detections.timestamp, pests.control_methods, detections.camera_index
        FROM detections
        JOIN pests ON detections.name = pests.name
    '''
    cursor.execute(query)
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections WHERE id = ?", (detection_id,))
    conn.commit()
    conn.close()

@app.route('/delete_all_detections', methods=['POST'])
def delete_all_detections():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM detections")  # ลบข้อมูลทั้งหมดในตาราง
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='detections'")  # รีเซ็ตลำดับ ID
        conn.commit()
        conn.close()
        return redirect(url_for('data'))  # กลับไปยังหน้าข้อมูลหลังจากลบเสร็จ
    except Exception as e:
        return f"An error occurred: {e}", 500

#data_image

@app.route('/data_image')
def data_image():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    query = '''
        SELECT image_detections.id, pests.name_thai, image_detections.name, image_detections.confidence, image_detections.timestamp, pests.control_methods
        FROM image_detections
        JOIN pests ON image_detections.name = pests.name
    '''
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    return render_template('data_image.html', data=rows)

@app.route('/delete_image_detection', methods=['POST'])
def delete_image_detection():
    detection_id = request.form.get('id')
    if detection_id:
        delete_image_detection_by_id(detection_id)
        return redirect(url_for('data_image'))
    return 'Error', 400

def delete_image_detection_by_id(detection_id):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM image_detections WHERE id = ?", (detection_id,))
    conn.commit()
    conn.close()

@app.route('/delete_all_image_detections', methods=['POST'])
def delete_all_image_detections():
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM image_detections")  # Delete all records
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='image_detections'")  # รีเซ็ตลำดับ ID
        conn.commit()
        conn.close()
        return redirect(url_for('data_image'))  # Redirect to the data page
    except Exception as e:
        return f"An error occurred: {e}", 500
    
#data_pest.html

@app.route('/pest_data')
def pest_data():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pests")
    rows = cursor.fetchall()
    conn.close()
    return render_template('pest_data.html', data=rows)


#index.html

@app.route('/')
def realtime():
    data = fetch_data_from_database()
    return render_template('realtime.html', random=time.time(), detections=data)

@app.route('/video_feed')
def video_feed():
    camera_index = int(request.args.get('camera_index', 0))  # รับ camera_index จาก query parameter
    return Response(generate_frames(camera_index), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_detections', methods=['GET'])
def get_detections():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections ORDER BY timestamp DESC")
    detections = cursor.fetchall()
    conn.close()
    return jsonify(detections=detections)


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
    conn = sqlite3.connect(DATABASE_PATH)
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
    conn = sqlite3.connect(DATABASE_PATH)
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM detections WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()











if __name__ == '__main__':
    if not os.path.exists('database'):
        os.makedirs('database')
    create_database()  # Ensure the database and table are created first
    update_schema()
    create_image_database()  # Ensure the database and table are created first
    create_pest_database()   # Ensure the pest database and table are created if not exists
    update_pest_schema()     # Update the pest schema
    if not os.path.exists('uploads'):
        os.makedirs('uploads')
    app.run(debug=True)