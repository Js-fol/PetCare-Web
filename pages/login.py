import re
import bcrypt
import streamlit as st
from sqlalchemy import text
from core.db import engine  # DB 경로/엔진은 core.db에서 관리

#간단한 이메일 검증
EMAIL_REGEX = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")

#세션 키 
SESSION_KEY = "auth_user"

def is_authenticated() -> bool:
    return SESSION_KEY in st.session_state

def set_user_session(user: dict):
    st.session_state[SESSION_KEY] = {"id": user["id"], "email": user["email"]}

def clear_user_session():
    st.session_state.pop(SESSION_KEY, None)

#로그인 검사 (DB 조회 + bcrypt)
def verify_login(email: str, password: str) -> tuple[bool, dict | None, str]:
    if not EMAIL_REGEX.match(email or ""):
        return False, None, "이메일 형식을 확인해 주세요."
    if not password:
        return False, None, "비밀번호를 입력해 주세요."

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT id, email, password_hash FROM users WHERE email = :e"),
            {"e": email.lower().strip()},
        ).mappings().first()

    if not row:
        return False, None, "존재하지 않는 이메일입니다."

    ok = False
    try:
        ok = bcrypt.checkpw(password.encode("utf-8"), row["password_hash"])
    except Exception:
        ok = False

    if not ok:
        return False, None, "비밀번호가 올바르지 않습니다."

    return True, {"id": row["id"], "email": row["email"]}, "로그인 성공"

# UI

st.title("로그인")

# 이미 로그인 상태라면
if is_authenticated():
    st.success(f"이미 로그인됨: {st.session_state[SESSION_KEY]['email']}")
    cols = st.columns(2)
    with cols[0]:
        st.page_link("pages/myprofile.py", label="프로필이 이미 있으신가요? 내 프로필 바로가기")
        st.page_link("pages/profile.py", label="프로필이 없으신가요? 프로필 등록 바로가기")
    with cols[1]:
        if st.button("로그아웃"):
            clear_user_session()
            st.rerun()
    st.stop()

# 로그인 폼
with st.form("login_form", clear_on_submit=False):
    email = st.text_input("이메일", placeholder="abc@example.com")
    password = st.text_input("비밀번호", type="password")
    submitted = st.form_submit_button("로그인")

if submitted:
    ok, user, msg = verify_login(email, password)
    if ok:
        set_user_session(user)
        st.success(msg)
        st.page_link("home.py", label="🏠 홈으로 이동")
    else:
        st.error(msg)

st.divider()

st.caption("아직 계정이 없으신가요?")
st.page_link("pages/signup.py", label="회원가입")
