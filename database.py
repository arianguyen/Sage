import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('plants.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS plants
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  species TEXT,
                  location TEXT,
                  notes TEXT,
                  status TEXT DEFAULT 'alive',
                  created_at TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS care_schedules
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  plant_id INTEGER,
                  task_type TEXT,
                  frequency_days INTEGER,
                  last_completed TEXT,
                  FOREIGN KEY (plant_id) REFERENCES plants(id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS wishlist
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  notes TEXT,
                  created_at TEXT)''')
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('plants.db')
    conn.row_factory = sqlite3.Row
    return conn