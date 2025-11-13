import streamlit as st
from sqlalchemy import text
from core.db import engine, init_db
import datetime as dt

init_db()  #DB 파일 및 테이블 생성

st.title("🐾 반려동물 프로필 등록")


#로그인 상태 확인 
SESSION_KEY="auth_user"
is_logged_in=SESSION_KEY in st.session_state
user=st.session_state.get(SESSION_KEY)


#입력 폼
if not is_logged_in or not user.get("id"):
    st.info("로그인이 필요합니다.")
    st.page_link("pages/login.py",label="로그인 페이지로 이동")
    st.stop()

species_map = {"🐶 강아지": "dog", "🐱 고양이": "cat"}
species_label = st.radio("반려동물 구분  (*필수)", list(species_map.keys()), horizontal=True)
species = species_map[species_label]

with st.form("pet_form"):
    name = st.text_input("이름  (*필수)" )
    breed = st.text_input("품종", placeholder="예: Korean Short Hair")
    birth = st.date_input("생일  (*필수)", min_value=dt.date(1900, 1, 1))
    notes = st.text_area("메모 (성격, 특이사항 등)")
    submitted = st.form_submit_button("등록")

if submitted:    #버튼이 눌렸으면
# 필수 정보 확인
    if name is None:
        st.warning("이름은 필수 입력 항목입니다. 모두 입력해주세요.")
    else:
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO pets(user_id, name, species, breed, birth, notes)
                    VALUES (:user_id, :name, :species, :breed, :birth, :notes)
                """),
                {
                    "user_id": int(user["id"]),
                    "name": f"{name}",  
                    "species": species,
                    "breed": breed if breed else None,
                    "birth": str(birth),
                    "notes": notes if notes else None
                })
        st.success(f"🐾 프로필 등록이 완료되었습니다 🐾")
        st.page_link("pages/myprofile.py", label="내 프로필로 이동")
        
   

