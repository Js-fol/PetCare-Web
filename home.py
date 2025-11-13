import streamlit as st
from core.db import init_db

init_db()  #db초기화 

st.set_page_config(page_title="🐾 PetCare", layout="wide")


#로그인 상태 확인 
SESSION_KEY="auth_user"
is_logged_in=SESSION_KEY in st.session_state
user=st.session_state.get(SESSION_KEY)

#메인홈페이지 제목 
st.title("🐾 나만의 PetCare 홈")
st.caption("좌측 Pages에서 기능을 선택하거나 아래 버튼으로 바로 이동하세요.")


#로그인 상태에 따른 화면 표시
if is_logged_in:
    st.success(f"반갑습니다!")
    if st.button("로그아웃"):
        del st.session_state[SESSION_KEY]
        st.rerun()

    st.subheader("내 반려동물 관리")
    st.page_link("pages/myprofile.py", label="내 프로필 관리", icon="🐾")
    st.page_link("pages/profile.py", label="반려동물 등록", icon="➕")
    st.page_link("pages/daily.py",label="반려동물 일일 기록",icon="📆")
    st.page_link("pages/calender.py",label="캘린더",icon="⏰")
    st.page_link("pages/album.py", label="포토 앨범",icon="📷")
else:
    st.info("로그인이 필요합니다. 아래 버튼으로 로그인 또는 회원가입을 진행하세요.")
    st.page_link("pages/login.py", label="로그인하기")
    st.page_link("pages/signup.py", label="회원가입하기")

