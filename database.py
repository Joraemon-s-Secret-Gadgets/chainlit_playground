# database.py
import sqlite3
import json

DB_PATH = "user_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            email TEXT,
            reset_token TEXT,
            resume_data TEXT
        )
    ''')

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
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def add_user_via_web(name: str, password_hash: str, email: str, resume_data: dict = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return False, "이미 가입된 이메일입니다."

    resume_json_str = json.dumps(resume_data, ensure_ascii=False) if resume_data else "{}"

    try:
        c.execute(
            'INSERT INTO users (username, password, email, resume_data) VALUES (?, ?, ?, ?)',
            (name, password_hash, email, resume_json_str)
        )
        conn.commit()
        return True, "가입 성공"
    except sqlite3.IntegrityError:
        return False, "데이터 처리 중 오류가 발생했습니다."
    finally:
        conn.close()

def update_resume_data(email: str, resume_data: dict) -> bool:
    """사용자의 resume_data를 업데이트합니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        resume_json_str = json.dumps(resume_data, ensure_ascii=False)
        c.execute(
            'UPDATE users SET resume_data = ? WHERE email = ?',
            (resume_json_str, email)
        )
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Resume Update Error: {e}")
        return False
    finally:
        conn.close()

def update_password(email: str, new_password_hash: str) -> bool:
    """사용자의 비밀번호를 업데이트합니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            'UPDATE users SET password = ?, reset_token = NULL WHERE email = ?',
            (new_password_hash, email)
        )
        conn.commit()
        return c.rowcount > 0
    except Exception as e:
        print(f"Password Update Error: {e}")
        return False
    finally:
        conn.close()

def save_chat_message(email: str, role: str, content: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute(
            'INSERT INTO chat_history (email, role, content) VALUES (?, ?, ?)',
            (email, role, content)
        )
        conn.commit()
    except Exception as e:
        print(f"Chat Save Error: {e}")
    finally:
        conn.close()

def load_chat_history(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'SELECT role, content FROM chat_history WHERE email = ? ORDER BY created_at ASC',
        (email,)
    )
    rows = c.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def delete_chat_history(email: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM chat_history WHERE email = ?', (email,))
    conn.commit()
    conn.close()