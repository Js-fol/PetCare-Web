import streamlit as st
from sqlalchemy import text
from core.auth import verify_login  

st.title("로그인")
#세션 키 
SESSION_KEY = "auth_user"

def is_authenticated() -> bool:
    return SESSION_KEY in st.session_state
def set_user_session(user: dict):
    st.session_state[SESSION_KEY] = {"id": user["id"], "email": user["email"]}
def clear_user_session():
    st.session_state.pop(SESSION_KEY, None)

#이미 로그인 상태
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
    ok, message, user = verify_login(email, password)
    if ok:
        set_user_session(user)
        st.success(message)
        st.page_link("home.py", label="🏠 홈으로 이동")
    else:
        st.error(message)

st.divider()

st.caption("아직 계정이 없으신가요?")
st.page_link("pages/signup.py", label="회원가입")
