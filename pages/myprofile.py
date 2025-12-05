from datetime import datetime, date
import streamlit as st
from sqlalchemy import text
from core.db import engine

st.title("🐾 내 프로필 관리")

#로그인 확인
SESSION_KEY = "auth_user"
user = st.session_state.get(SESSION_KEY)
if not user:
    st.warning("로그인이 필요합니다.")
    st.page_link("pages/login.py",label="로그인 페이지로 이동")
    st.stop()
user_id = user["id"] 

#반려동물 목록 가져오기(pets 테이블)
def get_pets_by_user(user_id: int) -> list[dict]:
    q = text("""
        SELECT id, name, species, breed, birth, notes
        FROM pets
        WHERE user_id = :uid
        ORDER BY id
    """)
    with engine.connect() as conn:
        rows = conn.execute(q, {"uid": user_id}).mappings().all()
        return [dict(r) for r in rows]

#날짜 표시 포맷
def fmt_date(d) -> str:
    try:
        if isinstance(d, str):
            d = datetime.fromisoformat(d).date()
        elif isinstance(d, datetime):
            d = d.date()
    except Exception:
        return str(d)

    today = date.today()

    years = today.year-d.year
    months = today.month-d.month
    
    #나이 계산
    formatted_date = d.strftime("%Y-%m-%d")
    age_str = f"{years}세 {months}개월" if years >= 0 else "나이 계산 불가"
    return f"{formatted_date} ({age_str})"
    
#강아지 고양이 아이콘 설정    
def species_icon(sp: str) -> str:
    return "🐶" if sp== "dog" else "🐱"
    
#프로필 삭제
def delete_pet(pet_id: int, user_id: int) -> bool:
    """현재 로그인 사용자의 소유 펫만 삭제"""
    try:
        with engine.begin() as conn:
            # 안전: FK on
            conn.execute(text("PRAGMA foreign_keys=ON"))
            res = conn.execute(
                text("DELETE FROM pets WHERE id = :pid AND user_id = :uid"),
                {"pid": pet_id, "uid": user_id},
            )
        return res.rowcount > 0
    except Exception as e:
        st.error(f"삭제 중 오류가 발생했습니다: {e}")
        return False

#화면 표시
pets = get_pets_by_user(user_id)

if not pets:
    st.info("등록된 반려동물이 없습니다.")
    st.page_link("pages/profile.py", label="➕ 반려동물 프로필 추가 등록")
    st.stop()

#여러 마리면 탭으로 구분
labels = [f"{species_icon(p.get('species'))} {p['name']}" for p in pets]

tabs = st.tabs(labels)

for p, tab in zip(pets, tabs):
    with tab:
        st.subheader(p["name"])

        icon = species_icon(p.get("species"))
        st.markdown(
            f"<div style='font-size:48px; line-height:1'>{icon}</div>",  #아이콘 크게 표시하는법
            unsafe_allow_html=True
        )

        cols = st.columns(1)
        with cols[0]:
            st.text(f"품종: {p.get('breed') or '-'}")

        st.write((fmt_date(p.get("birth"))))

        #메모 표시
        if p.get("notes"):
            with st.expander("메모 보기"):
                st.write(p["notes"])
    
        #프로필 삭제
        with st.expander("🗑️ 프로필 삭제 (되돌릴 수 없어요)"):
            with st.form(f"delete_form_{p['id']}"):
                st.warning("정말 삭제하시겠어요? 삭제하면 이 반려동물의 프로필 데이터가 영구히 제거됩니다.")
                confirm = st.checkbox("네, 삭제에 동의합니다.")
                delete_clicked = st.form_submit_button("프로필 삭제", type="primary")

            if delete_clicked:
                if not confirm:
                    st.info("삭제가 취소되었습니다. 확인 체크박스를 먼저 선택해 주세요.")
                else:
                    ok = delete_pet(pet_id=p["id"], user_id=user_id)
                    if ok:
                        st.success("삭제되었습니다.")
                        st.rerun()  
                    else:
                        st.error("삭제할 수 없습니다. (권한 문제이거나 이미 삭제되었을 수 있어요.)")

    

st.divider()
st.page_link("pages/profile.py", label="➕ 반려동물 프로필 추가 등록")
