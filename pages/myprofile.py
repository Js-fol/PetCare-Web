from datetime import datetime, date
import streamlit as st
from sqlalchemy import text
from core.db import engine, init_db

# 설정 (질문에서 주신 DB 경로 방식과 동일)
SESSION_KEY = "auth_user"  #로그인 세션 키

if "auth_user" not in st.session_state and "user" in st.session_state:
    st.session_state["auth_user"] = st.session_state["user"]


init_db()

# 유틸 함수
def is_logged_in() -> bool:
    u = st.session_state.get(SESSION_KEY)
    return isinstance(u, dict) and ("id" in u and u["id"] is not None) and bool(u.get("email"))

def require_login():
    if not is_logged_in():
        st.error("로그인이 필요합니다.")
        # page_link 경로가 앱 구조에 맞는지 확인 (pages/ 하위라면 아래처럼)
        st.page_link("pages/login.py", label="로그인 페이지로 이동")
        st.stop()

def get_user_by_email(email: str) -> dict | None:
    q = text("""
        SELECT id, email
        FROM users
        WHERE email = :email
        LIMIT 1
    """)
    with engine.connect() as conn:
        row = conn.execute(q, {"email": email}).mappings().first()
        return dict(row) if row else None

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

def fmt_date(d) -> str:
    try:
        if isinstance(d, str):
            d = datetime.fromisoformat(d).date()
        elif isinstance(d, datetime):
            d = d.date()
    except Exception:
        return str(d)

    today = date.today()

    years = today.year - d.year
    months = today.month - d.month
    
    # 날짜 + 나이 표시
    formatted_date = d.strftime("%Y-%m-%d")
    age_str = (f"{years}세 {months}개월")
    return (f"{formatted_date} ({age_str})")
    
    
def species_icon(sp: str) -> str:
    return "🐶" if sp== "dog" else "🐱"
    

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

#화면
st.set_page_config(page_title="내 프로필", page_icon="🐾")


require_login()

email = st.session_state[SESSION_KEY]["email"]
user_id = st.session_state[SESSION_KEY]["id"]
st.caption(f"로그인 계정: {email}")

pets = get_pets_by_user(user_id)

if not pets:
    st.info("등록된 반려동물이 없습니다.")
    st.page_link("pages/profile.py", label="➕ 반려동물 프로필 추가 등록")
    st.stop()

# 여러 마리면 탭으로 구분
labels = [f"{'🐶' if p.get('species')=='dog' else '🐱'} {p['name']}" for p in pets]

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
            st.metric("품종", p.get("breed") or "-")
       

        st.write((fmt_date(p.get("birth"))))

        # 메모가 있으면 접어서 보기
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
                        st.rerun()   # 최신 Streamlit
                    else:
                        st.error("삭제할 수 없습니다. (권한 문제이거나 이미 삭제되었을 수 있어요.)")

    

st.divider()

st.page_link("pages/profile.py", label="➕ 반려동물 프로필 추가 등록")
