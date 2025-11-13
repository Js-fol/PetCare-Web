import re
import bcrypt
import streamlit as st
from sqlalchemy import text
from core.db import engine

st.title("회원가입")

#이메일 형식 검사 
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match((email or "").strip()))

def validate_password(pw: str) -> tuple[bool, str]:
    if not pw or len(pw) < 8:
        return False, "비밀번호는 8자 이상이어야 합니다."
    if not any(c.isdigit() for c in pw):
        return False, "비밀번호에 숫자를 최소 1개 포함하세요."
    if not any(c.isalpha() for c in pw):
        return False, "비밀번호에 영문자를 최소 1개 포함하세요."
    return True, ""

def normalize_email(email: str) -> str:
    return (email or "").strip().lower()

#회원가입 폼
with st.form("signup_form", clear_on_submit=False):
    email = st.text_input("이메일")
    pw = st.text_input("비밀번호", type="password", help="8자이상, 영문+숫자 포함")
    pw2 = st.text_input("비밀번호 확인", type="password")
    submitted = st.form_submit_button("가입하기")

if submitted:
    email_n = normalize_email(email)

    #검증
    if not is_valid_email(email_n):
        st.error("이메일 형식을 확인해 주세요.")
        st.stop()
    ok, msg = validate_password(pw)
    if not ok:
        st.error(msg)
        st.stop()
    if pw != pw2:
        st.error("비밀번호가 서로 일치하지 않습니다.")
        st.stop()

    #중복 이메일 확인
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT id FROM users WHERE email = :e"),
            {"e": email_n},
        ).fetchone()

    if exists:
        st.error("이미 등록된 이메일입니다.")
        st.stop()

    #비밀번호 해시 생성 + DB 저장
    try:
        pw_hash = bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt(rounds=12))
        with engine.begin() as conn:
            conn.execute(
                text("INSERT INTO users(email, password_hash) VALUES (:e, :p)"),
                {"e": email_n, "p": pw_hash},
            )
        st.success("회원가입이 완료되었습니다. 이제 로그인해 주세요.")
        st.page_link("pages/login.py", label="로그인 하러가기")
        st.balloons()
    except Exception as e:
        st.error(f"회원가입 중 오류가 발생했습니다: {e}")

