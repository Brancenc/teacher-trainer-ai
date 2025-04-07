import sqlite3
import json

db_path = "chat-memory.sqlite"

def create_table():
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        cursor = conn.cursor()
        cursor.execute('''  
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, 
                conversations TEXT,
                grade_level TEXT,
                subject TEXT,
                challenge TEXT
            )    
        ''')
        conn.commit()

def retrieve_chats(username):
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, conversations, grade_level, subject, challenge
            FROM chat_sessions
            WHERE username = ?
                       
        ''', (username,))
        rows = cursor.fetchall()
        if not rows:
            return None
        else:
            return rows
        
def store_chat(username, chat, g_level="2nd", subj="math", chal="disruptive"):
    chat_json = json.dumps(chat)
    with sqlite3.connect(db_path, timeout=5.0) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chat_sessions (username, conversations, grade_level, subject, challenge)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, chat_json, g_level, subj, chal))
        conn.commit()
