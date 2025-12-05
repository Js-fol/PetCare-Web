import re
import bcrypt
from sqlalchemy import text
from core.db import engine

#이메일 형식 설정
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def is_valid_email(email: str) -> bool:  #이메일 형식 검사
    return bool(EMAIL_RE.match((email or "").strip()))

#비밀번호 형식 설정
def validate_password(pw: str) -> tuple[bool, str]:
    if not pw or len(pw) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다."
    if not any(c.isdigit() for c in pw):
        return False, "비밀번호에 숫자를 최소 1개 포함하세요."
    if not any(c.isalpha() for c in pw):
        return False, "비밀번호에 영문자를 최소 1개 포함하세요."
    return True, ""

#비밀번호 유틸
def hash_password(password: str) -> bytes:  #비밀번호를 bcrypt 해시로 변환
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))

def check_password(password: str, hashed: bytes) -> bool:  #입력한 비밀번호가 해시와 일치하는지 확인
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except Exception:
        return False

#회원가입
def create_user(email: str, password: str) -> tuple[bool, str]:
    #이메일 형식 검사
    if not is_valid_email(email):
        return False,"이메일 형식을 확인해 주세요."
    
    #비밀번호 형식 검사
    ok, message=validate_password(password)
    if not ok:
        return False, message
    
    #이메일 중복 검사
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": email.lower().strip()},
        ).fetchone()

        if exists:
            return False, "이미 등록된 이메일입니다."

        #비밀번호 해시 생성
        hashed = hash_password(password)

        #DB 저장
        conn.execute(
            text("INSERT INTO users(email, password_hash) VALUES (:e, :p)"),
                {"e": email.lower().strip(), "p": hashed},
            )
    return True, "회원가입이 완료되었습니다."

#로그인
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

        #로그인 성공
        return True, "로그인 성공", {"id": row["id"], "email": row["email"]}
