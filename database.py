# database.py
import sqlite3

DB_PATH = "user_data.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        # users 테이블 확장 (이메일, 리셋 토큰, 프로필 정보 등 모두 포함)
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT,
                email TEXT UNIQUE,
                reset_token TEXT,
                edu TEXT, exp TEXT, awd TEXT,
                role TEXT DEFAULT 'user'
            )
        ''')
        conn.commit()

# ==========================================
#  로그인 시 유저 정보를 가져오는 함수
# ==========================================
def get_user(username: str):
    """DB에서 특정 유저 정보를 가져옵니다."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        return c.fetchone()

# ==========================================
# 자소서 첨삭용 프로필 업데이트 함수
# ==========================================
def update_user_profile(username, edu, exp, awd):
    """유저의 프로필(학력, 경력, 수상)을 업데이트합니다."""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET edu=?, exp=?, awd=? WHERE username=?", (edu, exp, awd, username))
        conn.commit()

# ==========================================
#  회원가입 웹페이지용 DB 삽입 함수
# ==========================================
def add_user_via_web(username, password, email):
    """웹 화면을 통한 회원가입 (중복 체크 포함)"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            # 아이디나 이메일이 겹치는지 사전 검증
            c.execute("SELECT username FROM users WHERE username=? OR email=?", (username, email))
            if c.fetchone():
                return False, "이미 존재하는 아이디 또는 이메일입니다."
            
            c.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)", 
                      (username, password, email))
            conn.commit()
            return True, "가입 성공"
    except sqlite3.IntegrityError:
        return False, "데이터베이스 무결성 오류 (중복 데이터)"
    except Exception as e:
        return False, f"서버 오류: {str(e)}"