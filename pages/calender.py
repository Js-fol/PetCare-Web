# pages/calendar.py
import streamlit as st
from sqlalchemy import text
from datetime import date
import calendar as cal
from core.db import engine, init_db

init_db()

st.title("⏰ 캘린더")

#로그인 확인
SESSION_KEY = "auth_user"
user = st.session_state.get(SESSION_KEY)
if not user:
    st.warning("로그인이 필요합니다.")
    st.page_link("pages/login.py",label="로그인 페이지로 이동")
    st.stop()
user_id = user["id"]

# 오늘/현재 월 상태
today = date.today()
if "cal_year" not in st.session_state:
    st.session_state.cal_year, st.session_state.cal_month = today.year, today.month
y, m = st.session_state.cal_year, st.session_state.cal_month

# 월 이동
c1, c2, c3, c4 = st.columns([1,1,1,6])
with c1:
    if st.button("◀ 이전달"):
        if m == 1:
            st.session_state.cal_year -= 1
            st.session_state.cal_month = 12
        else:
            st.session_state.cal_month -= 1
        st.rerun()
with c2:
    if st.button("이번달"):
        st.session_state.cal_year, st.session_state.cal_month = today.year, today.month
        st.session_state.selected_date = today
        st.rerun()
with c3:
    if st.button("다음달 ▶"):
        if m == 12:
            st.session_state.cal_year += 1
            st.session_state.cal_month = 1
        else:
            st.session_state.cal_month += 1
        st.rerun()
with c4:
    st.markdown(f"### {y}년 {m}월")

# 이번 달 일정 불러오기
with engine.begin() as conn:
    events = conn.execute(
        text("""
        SELECT id, event_date, title
        FROM events
        WHERE user_id = :uid
          AND strftime('%Y', event_date) = :y
          AND strftime('%m', event_date) = :m
        ORDER BY event_date, id
        """),
        {"uid": user_id, "y": str(y), "m": f"{m:02d}"}
    ).fetchall()

#날짜별로 그룹화
events_by_day = {}
for ev in events:
    d = str(ev.event_date)
    events_by_day.setdefault(d, []).append((ev.id, ev.title))

#캘린더 표시
cal.setfirstweekday(cal.MONDAY)
month_matrix = cal.monthcalendar(y, m)
weekdays = ["월", "화", "수", "목", "금", "토", "일"]

hdr = st.columns(7)
for i, w in enumerate(weekdays):
    hdr[i].markdown(f"**{w}**")

for week in month_matrix:
    cols = st.columns(7)
    for i, day_num in enumerate(week):
        cell = cols[i].container(border=True)
        if day_num == 0:
            cell.write(" ")
            continue

        d_str = f"{y}-{m:02d}-{day_num:02d}"
        is_today = (d_str == today.strftime("%Y-%m-%d"))

        # 날짜 숫자
        if is_today:
            cell.markdown(f"<div style='font-weight:700;color:#2563eb'>{day_num}</div>", unsafe_allow_html=True)
        else:
            cell.markdown(f"**{day_num}**")

        # 일정 미리보기 (각 셀)
        for _, title in events_by_day.get(d_str, [])[:3]:
            short = title if len(title) <= 10 else title[:10] + "…"
            cell.markdown(f"{short}")

# 선택한 날짜 섹션
st.markdown("---")
st.subheader("✍️ 일정 등록 / 삭제")
colL, colR = st.columns([2,3])

# 날짜 선택 (여기서 등록/목록 관리)
with colL:
    sel_date = st.date_input("날짜 선택", value=today)
    with st.form("add_event_form", clear_on_submit=True):
        title = st.text_input("일정", placeholder="예: 접종 / 병원 / 미용 / 메모 등")
        submit = st.form_submit_button("➕ 등록")
        if submit:
            if not title.strip():
                st.warning("일정을 입력해 주세요.")
            else:
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                        INSERT INTO events (user_id, event_date, title, updated_at)
                        VALUES (:uid, :d, :title, CURRENT_TIMESTAMP)
                        """),
                        {"uid": user_id, "d": sel_date.isoformat(), "title": title.strip()}
                    )
                st.success("등록되었습니다.")
                st.rerun()

#일정삭제
with colR:
    st.write(f"**{sel_date.strftime('%Y-%m-%d')} 일정**")
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
            SELECT id, title
            FROM events
            WHERE user_id=:uid AND event_date=:d
            ORDER BY id
            """),
            {"uid": user_id, "d": sel_date.isoformat()}
        ).fetchall()

    if not rows:
        st.info("등록된 일정이 없습니다.")
    else:
        for ev_id, ev_title in rows:
            c1, c2 = st.columns([8,1])
            c1.markdown(f"- **{ev_title}**")
            if c2.button("삭제", key=f"del-{ev_id}"):
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM events WHERE id=:id AND user_id=:uid"),
                                 {"id": ev_id, "uid": user_id})
                st.success("삭제했습니다.")
                st.rerun()