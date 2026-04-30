import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "garden.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Benim Bahçem tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS my_garden
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER,
                  nickname TEXT,
                  added_date TEXT,
                  last_watered TEXT,
                  last_fertilized TEXT,
                  is_sick INTEGER DEFAULT 0,
                  treatment_start_date TEXT)''')
    
    # Bakım Günlüğü tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS plant_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  garden_id INTEGER,
                  log_date TEXT,
                  log_type TEXT,
                  note TEXT,
                  image_path TEXT)''')
    
    # Ajan Ayarları ve Durumu
    c.execute('''CREATE TABLE IF NOT EXISTS agent_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  setting_key TEXT UNIQUE,
                  setting_value TEXT)''')
    
    # Öğrenilen Bilgiler (Self-Optimizing DB)
    c.execute('''CREATE TABLE IF NOT EXISTS learned_knowledge
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER,
                  knowledge_type TEXT,
                  content TEXT,
                  confidence REAL,
                  last_updated TEXT)''')
    
    conn.commit()
    conn.close()

def add_to_garden(plant_id, nickname):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.date.today().isoformat()
    c.execute("INSERT INTO my_garden (plant_id, nickname, added_date, last_watered, last_fertilized) VALUES (?, ?, ?, ?, ?)",
              (plant_id, nickname, now, now, now))
    conn.commit()
    conn.close()

def get_my_garden():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM my_garden")
    rows = c.fetchall()
    conn.close()
    return rows

def update_care(garden_id, care_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.date.today().isoformat()
    if care_type == "water":
        c.execute("UPDATE my_garden SET last_watered = ? WHERE id = ?", (now, garden_id))
    elif care_type == "fertilize":
        c.execute("UPDATE my_garden SET last_fertilized = ? WHERE id = ?", (now, garden_id))
    elif care_type == "diagnose":
        c.execute("UPDATE my_garden SET is_sick = 1, treatment_start_date = ? WHERE id = ?", (now, garden_id))
    elif care_type == "heal":
        c.execute("UPDATE my_garden SET is_sick = 0, treatment_start_date = NULL WHERE id = ?", (garden_id))
    
    # Log ekle
    c.execute("INSERT INTO plant_logs (garden_id, log_date, log_type) VALUES (?, ?, ?)", (garden_id, now, care_type))
    
    conn.commit()
    conn.close()

def add_log(garden_id, note, image_path=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.date.today().isoformat()
    c.execute("INSERT INTO plant_logs (garden_id, log_date, log_type, note, image_path) VALUES (?, ?, ?, ?, ?)",
              (garden_id, now, "diary", note, image_path))
    conn.commit()
    conn.close()

def get_logs(garden_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM plant_logs WHERE garden_id = ? ORDER BY log_date DESC", (garden_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def update_learned_knowledge(plant_id, k_type, content, confidence):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.date.today().isoformat()
    c.execute("""INSERT INTO learned_knowledge (plant_id, knowledge_type, content, confidence, last_updated)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(id) DO UPDATE SET content=excluded.content, confidence=excluded.confidence, last_updated=excluded.last_updated""",
              (plant_id, k_type, content, confidence, now))
    conn.commit()
    conn.close()

def get_learned_knowledge(plant_id=None):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    if plant_id:
        c.execute("SELECT * FROM learned_knowledge WHERE plant_id = ?", (plant_id,))
    else:
        c.execute("SELECT * FROM learned_knowledge")
    rows = c.fetchall()
    conn.close()
    return rows

def set_agent_setting(key, value):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO agent_settings (setting_key, setting_value) VALUES (?, ?) ON CONFLICT(setting_key) DO UPDATE SET setting_value=excluded.setting_value", (key, value))
    conn.commit()
    conn.close()

def get_agent_setting(key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT setting_value FROM agent_settings WHERE setting_key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None
