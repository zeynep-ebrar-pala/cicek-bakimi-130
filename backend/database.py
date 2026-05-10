import sqlite3
import datetime
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_NAME = os.path.join(BASE_DIR, "garden.db")

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Kullanıcı Profili (API Key vb.)
    c.execute('''CREATE TABLE IF NOT EXISTS user_profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT DEFAULT 'Bitki Sever',
                  api_key TEXT,
                  groq_api_key TEXT,
                  joined_date TEXT)''')

    # Migration: Eksik sütunları ekle
    try:
        c.execute("ALTER TABLE user_profiles ADD COLUMN groq_api_key TEXT")
    except sqlite3.OperationalError: pass

    # Benim Bahçem tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS my_garden
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER,
                  nickname TEXT,
                  added_date TEXT,
                  last_watered TEXT,
                  last_fertilized TEXT,
                  is_sick INTEGER DEFAULT 0,
                  treatment_start_date TEXT,
                  user_api_key TEXT)''')
    
    # Bakım Günlüğü tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS plant_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  garden_id INTEGER,
                  log_date TEXT,
                  log_type TEXT,
                  note TEXT,
                  image_path TEXT)''')
    
    # Günün Bitkisi Takibi
    c.execute('''CREATE TABLE IF NOT EXISTS daily_plant
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER,
                  selection_date TEXT UNIQUE)''')

    # Ajan Ayarları
    c.execute('''CREATE TABLE IF NOT EXISTS agent_settings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  setting_key TEXT UNIQUE,
                  setting_value TEXT)''')
    
    # Migration: Eksik sütunları ekle
    try:
        c.execute("ALTER TABLE my_garden ADD COLUMN user_api_key TEXT")
    except sqlite3.OperationalError: pass
    
    conn.commit()
    conn.close()

def get_user_profile():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM user_profiles LIMIT 1")
    row = c.fetchone()
    if not row:
        now = datetime.date.today().isoformat()
        c.execute("INSERT INTO user_profiles (username, joined_date) VALUES (?, ?)", ("Bitki Sever", now))
        conn.commit()
        c.execute("SELECT * FROM user_profiles LIMIT 1")
        row = c.fetchone()
    conn.close()
    return row

def update_user_profile(username, api_key, groq_api_key=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE user_profiles SET username = ?, api_key = ?, groq_api_key = ?", (username, api_key, groq_api_key))
    conn.commit()
    conn.close()

def get_daily_plant_id():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.date.today().isoformat()
    c.execute("SELECT plant_id FROM daily_plant WHERE selection_date = ?", (today,))
    row = c.fetchone()
    if not row:
        from data import PLANTS
        import random
        p_id = random.choice(PLANTS)["id"]
        c.execute("INSERT OR REPLACE INTO daily_plant (plant_id, selection_date) VALUES (?, ?)", (p_id, today))
        conn.commit()
        return p_id
    conn.close()
    return row[0]

def add_to_garden(plant_id, nickname, api_key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.date.today().isoformat()
    c.execute("INSERT INTO my_garden (plant_id, nickname, added_date, last_watered, last_fertilized, user_api_key) VALUES (?, ?, ?, ?, ?, ?)",
              (plant_id, nickname, now, now, now, api_key))
    conn.commit()
    conn.close()

def remove_from_garden(garden_id, api_key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM my_garden WHERE id = ? AND user_api_key = ?", (garden_id, api_key))
    conn.commit()
    conn.close()

def get_my_garden(api_key):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM my_garden WHERE user_api_key = ?", (api_key,))
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
