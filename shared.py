# shared.py

import os
import sqlite3
import time
import torch

model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt', force_reload=True)

classNames = ['Atlas-moth', 'Black-Grass-Caterpillar', 'Coconut-black-headed-caterpillar', 'Common cutworm', 'Cricket', 'Diamondback-moth',
         'Fall-Armyworm', 'Grasshopper', 'Green-weevil', 'Leaf-eating-caterpillar', 'Oriental-Mole-Cricket', 'Oriental-fruit-fly',
          'Oryctes-rhinoceros', 'Red cotton steiner', 'Rice-Bug', 'Stem-borer', 'The-Plain-Tiger', 'White-grub']

DATABASE_PATH = 'database/databasev5.db'
PEST_DATABASE_PATH = 'database/database_pest.db'

def create_database():
    conn = sqlite3.connect(DATABASE_PATH)
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
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    current_timestamp = time.strftime('%H:%M:%S')  # Format time as hours:minutes:seconds
    cursor.execute("INSERT INTO detections (name, confident, timestamp) VALUES (?, ?, ?)",
                   (name, confident, current_timestamp))
    conn.commit()
    conn.close()

def fetch_data_from_database():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections")
    data = cursor.fetchall()
    conn.close()
    return data

def update_schema():
    conn = sqlite3.connect(DATABASE_PATH)
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

# shared.py

def create_pest_database():
    if not os.path.exists(PEST_DATABASE_PATH):
        conn = sqlite3.connect(PEST_DATABASE_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_name TEXT NOT NULL,
                thai_name TEXT,
                description TEXT,
                outbreak_period TEXT,
                food_plants TEXT,
                control_methods TEXT
            )
        ''')
        conn.commit()
        conn.close()
    else:
        print("Database already exists, skipping creation.")

def update_pest_schema():
    conn = sqlite3.connect(PEST_DATABASE_PATH)
    cursor = conn.cursor()

    # ตรวจสอบว่าตารางมีอยู่หรือไม่
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pests'")
    if cursor.fetchone() is None:
        print("Table 'pests' does not exist. Skipping schema update.")
        conn.close()
        return

    try:
        # เพิ่มคอลัมน์ใหม่ถ้ายังไม่มีอยู่
        cursor.execute("ALTER TABLE pests ADD COLUMN english_name TEXT")
        cursor.execute("ALTER TABLE pests ADD COLUMN thai_name TEXT")
        cursor.execute("ALTER TABLE pests ADD COLUMN description TEXT")
        cursor.execute("ALTER TABLE pests ADD COLUMN outbreak_period TEXT")
        cursor.execute("ALTER TABLE pests ADD COLUMN food_plants TEXT")
        cursor.execute("ALTER TABLE pests ADD COLUMN control_methods TEXT")
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error updating schema: {e}")

    conn.close()
