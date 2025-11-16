import streamlit as st
from core.auth import create_user

st.title("회원가입")

#회원가입 폼
with st.form("signup_form", clear_on_submit=False):
    email = st.text_input("이메일")
    pw = st.text_input("비밀번호", type="password", help="8자이상, 영문+숫자 포함")
    pw2 = st.text_input("비밀번호 확인", type="password")
    submitted = st.form_submit_button("가입하기")

if submitted:
    if pw != pw2:
        st.error("비밀번호가 서로 일치하지 않습니다.")
        st.stop()

    ok, message = create_user(email, pw)

    if not ok:
        st.error(message)
    else:
        st.success("회원가입이 완료되었습니다. 이제 로그인해 주세요.")
        st.page_link("pages/login.py", label="로그인 하러가기")
        st.balloons()
