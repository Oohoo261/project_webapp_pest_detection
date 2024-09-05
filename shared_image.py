import sqlite3
import torch

model = torch.hub.load('ultralytics/yolov5', 'custom', path='best.pt', force_reload=True)

classNames = ['Atlas-moth', 'Black-Grass-Caterpillar', 'Coconut-black-headed-caterpillar', 'Common cutworm', 'Cricket', 'Diamondback-moth',
         'Fall-Armyworm', 'Grasshopper', 'Green-weevil', 'Leaf-eating-caterpillar', 'Oriental-Mole-Cricket', 'Oriental-fruit-fly',
          'Oryctes-rhinoceros', 'Red cotton steiner', 'Rice-Bug', 'Stem-borer', 'The-Plain-Tiger', 'White-grub']

IMAGE_DATABASE_PATH = 'database/database_image.db'

def create_image_database():
    conn = sqlite3.connect(IMAGE_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS image_detections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        confidence REAL,
                        timestamp TEXT
                    )''')
    conn.commit()
    conn.close()

def insert_image_detection(name, confidence, timestamp):
    conn = sqlite3.connect(IMAGE_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO image_detections (name, confidence, timestamp) VALUES (?, ?, ?)', 
                   (name, confidence, timestamp))
    conn.commit()
    conn.close()

def fetch_image_data_from_database():
    conn = sqlite3.connect(IMAGE_DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM image_detections")
    data = cursor.fetchall()
    conn.close()
    return data

def update_image_schema():
    conn = sqlite3.connect(IMAGE_DATABASE_PATH)
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