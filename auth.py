# auth.py
import hashlib
import secrets

def hash_pw(password: str) -> str:
    """비밀번호를 단방향 암호화(SHA-256) 합니다."""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_reset_token() -> str:
    """비밀번호 찾기용 1회용 랜덤 토큰을 생성합니다."""
    return secrets.token_urlsafe(32)