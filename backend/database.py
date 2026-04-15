import sqlite3
import json
import os

DB_PATH = "user_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 유저 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT,
            password TEXT,
            email TEXT PRIMARY KEY,
            reset_token TEXT,
            resume_data TEXT 
        )
    ''')
    # 채팅 내역 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_user(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, password, email, reset_token, resume_data FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def add_user_via_web(name, password_hash, email, resume_data=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return False, "이미 가입된 이메일입니다."
    
    resume_json_str = json.dumps(resume_data, ensure_ascii=False) if resume_data else "{}"
    try:
        c.execute('INSERT INTO users (username, password, email, resume_data) VALUES (?, ?, ?, ?)', 
                  (name, password_hash, email, resume_json_str))
        conn.commit()
        return True, "회원가입 성공"
    except Exception as e:
        return False, f"오류 발생: {e}"
    finally:
        conn.close()

def update_password(email, new_password_hash):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET password = ? WHERE email = ?', (new_password_hash, email))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_resume_data(email, resume_data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    resume_json_str = json.dumps(resume_data, ensure_ascii=False)
    c.execute('UPDATE users SET resume_data = ? WHERE email = ?', (resume_json_str, email))
    success = c.rowcount > 0
    conn.commit()
    conn.close()
    return success

def save_chat_message(email, role, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO chat_history (email, role, content) VALUES (?, ?, ?)', (email, role, content))
    conn.commit()
    conn.close()

def load_chat_history(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT role, content FROM chat_history WHERE email = ? ORDER BY created_at ASC', (email,))
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def delete_chat_history(email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM chat_history WHERE email = ?', (email,))
    conn.commit()
    conn.close()