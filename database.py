# database.py
import sqlite3
import json

DB_PATH = "user_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. 기존 유저 테이블
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            email TEXT,
            reset_token TEXT,
            resume_data TEXT 
        )
    ''')

    # ✅ 2. 채팅 기록 테이블 추가
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,          -- 사용자 식별용
            role TEXT NOT NULL,           -- 'user' 또는 'assistant'
            content TEXT NOT NULL,        -- 메시지 내용
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# --- 기존 함수들 (get_user, add_user_via_web 등) ---
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
        c.execute('INSERT INTO users (username, password, email, resume_data) VALUES (?, ?, ?, ?)', 
                  (name, password_hash, email, resume_json_str))
        conn.commit()
        return True, "가입 성공"
    except sqlite3.IntegrityError:
        return False, "데이터 처리 중 오류가 발생했습니다."
    finally:
        conn.close()

# ✅ 추가: 채팅 관련 신규 함수들
def save_chat_message(email: str, role: str, content: str):
    """새로운 메시지를 DB에 저장합니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('INSERT INTO chat_history (email, role, content) VALUES (?, ?, ?)', 
                  (email, role, content))
        conn.commit()
    except Exception as e:
        print(f"Chat Save Error: {e}")
    finally:
        conn.close()

def load_chat_history(email: str):
    """특정 사용자의 전체 대화 내역을 불러옵니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 과거 메시지부터 순서대로 불러옵니다.
    c.execute('SELECT role, content FROM chat_history WHERE email = ? ORDER BY created_at ASC', (email,))
    rows = c.fetchall()
    conn.close()
    
    # Streamlit 세션 형식으로 변환하여 반환
    return [{"role": row[0], "content": row[1]} for row in rows]

def delete_chat_history(email: str):
    """대화 초기화 기능이 필요할 때 사용합니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM chat_history WHERE email = ?', (email,))
    conn.commit()
    conn.close()