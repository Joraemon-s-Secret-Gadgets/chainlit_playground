# database.py
import sqlite3
import json

DB_PATH = "user_data.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # resume_data: 비정형 이력서 데이터를 저장하는 JSON 컬럼
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT,
            email TEXT,
            reset_token TEXT,
            resume_data TEXT 
        )
    ''')
    conn.commit()
    conn.close()

def get_user(email: str):
    """이메일(아이디)로 사용자 정보를 가져옵니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    user = c.fetchone()
    conn.close()
    return user

def add_user_via_web(name: str, password_hash: str, email: str, resume_data: dict = None):
    """새로운 사용자를 등록합니다. (이메일 중복 체크 포함)"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 이메일 중복 확인
    c.execute('SELECT * FROM users WHERE email = ?', (email,))
    if c.fetchone():
        conn.close()
        return False, "이미 가입된 이메일입니다."
    
    resume_json_str = json.dumps(resume_data, ensure_ascii=False) if resume_data else "{}"

    try:
        # username 자리에 이름을, email 자리에 이메일을 넣습니다.
        c.execute('INSERT INTO users (username, password, email, resume_data) VALUES (?, ?, ?, ?)', 
                  (name, password_hash, email, resume_json_str))
        conn.commit()
        return True, "가입 성공"
    except sqlite3.IntegrityError:
        return False, "데이터 처리 중 오류가 발생했습니다."
    finally:
        conn.close()

def update_resume_data(email: str, resume_data: dict):
    """마이페이지의 이력서 정보를 업데이트합니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    resume_json_str = json.dumps(resume_data, ensure_ascii=False)
    
    try:
        c.execute('UPDATE users SET resume_data = ? WHERE email = ?', (resume_json_str, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Update Error: {e}")
        return False
    finally:
        conn.close()

def update_password(email: str, new_password_hash: str):
    """비밀번호 찾기 기능을 위한 비밀번호 재설정 함수입니다."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('UPDATE users SET password = ? WHERE email = ?', (new_password_hash, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Password Update Error: {e}")
        return False
    finally:
        conn.close()