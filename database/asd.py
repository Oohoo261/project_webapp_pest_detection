import sqlite3

# ระบุพาธของฐานข้อมูลของคุณ
db_path = 'D:/project/project_webapp_pest_detection/database/databasev5.db'

# เชื่อมต่อกับฐานข้อมูล
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# ลบตาราง pests_new
cursor.execute('DROP TABLE IF EXISTS pests_new')

# บันทึกการเปลี่ยนแปลงและปิดการเชื่อมต่อ
conn.commit()
conn.close()

print("Table 'pests_new' has been deleted.")
