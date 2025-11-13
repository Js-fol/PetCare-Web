import bcrypt
from sqlalchemy import text
from core.db import engine

#비밀번호 관련 유틸
def hash_password(password: str) -> bytes:
    """비밀번호를 bcrypt 해시로 변환"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

def check_password(password: str, hashed: bytes) -> bool:
    """입력한 비밀번호가 해시와 일치하는지 확인"""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except Exception:
        return False

#회원가입 로직
def create_user(email: str, password: str) -> tuple[bool, str]:
    """회원가입: 이메일 중복 확인 + 해시 저장"""
    # 이메일 중복 검사
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": email.lower().strip()},
        ).fetchone()

        if exists:
            return False, "이미 등록된 이메일입니다."

        # 비밀번호 해시 생성
        hashed = hash_password(password)

        # DB 저장
        conn.execute(
            text("INSERT INTO users(email, password_hash) VALUES (:e, :p)"),
            {"e": email.lower().strip(), "p": hashed},
        )
        return True, "회원가입이 완료되었습니다."

#로그인 로직

def verify_login(email: str, password: str) -> tuple[bool, str, dict | None]:
    """로그인 시 이메일/비밀번호 검증"""
    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT id, email, password_hash FROM users WHERE email = :e"),
            {"e": email.lower().strip()},
        ).mappings().first()

        if not row:
            return False, "존재하지 않는 이메일입니다.", None

        if not check_password(password, row["password_hash"]):
            return False, "비밀번호가 일치하지 않습니다.", None

        # 로그인 성공
        return True, "로그인 성공", {"id": row["id"], "email": row["email"]}
