import streamlit as st
import pandas as pd
from datetime import date
from sqlalchemy import text
from core.db import engine, init_db
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

SESSION_KEY="auth_user"

init_db()

#적정량 계산
def calc_targets(species: str, current_weight_kg: float) -> dict:
    species = (species or "").lower()
    w = max(current_weight_kg or 0.0, 0.0)
    if species == "cat":
        return {
            "food_g": 22.5 * w,      
            "water_ml": 55.0 * w,   
            "activity_min": 20.0,   
        }
    else:  #dog
        return {
            "food_g": 20.0 * w,       
            "water_ml": 60.0 * w,     
            "activity_min": 60.0,     
        }

#적정 여부 판정 (±10% 허용구간)
def judge(value, target, tol_ratio_low=0.7, tol_ratio_high=1.3):
    if value is None or target is None or target <= 0:
        return "—"
    if value < target * tol_ratio_low:
        return "🚨 부족 🚨"
    if value > target * tol_ratio_high:
        return "⚠️ 과다 ⚠️"
    return "✅ 적정 ✅"

st.title("📆 반려동물 일일 기록")
st.caption("몸무게, 사료량, 음수량, 활동량을 기록하고 적정 여부와 최근 몸무게 변화를 확인합니다.")

user = st.session_state.get(SESSION_KEY)
if not user:
    st.warning("로그인이 필요합니다.")
    st.page_link("pages/login.py", label="로그인 페이지로 이동")
    st.stop()
user_id = user["id"]

#펫 목록
with engine.begin() as conn:
    pets = conn.execute(
        text("SELECT id, name, species, weight FROM pets WHERE user_id=:uid ORDER BY name"),
        {"uid": user_id}
    ).fetchall()

if not pets:
    st.info("등록된 반려동물이 없습니다. 먼저 프로필을 등록해 주세요.")
    st.stop()

#이름으로 보여주되 내부적으로는 id 사용
pet_map = {f"{p.name} ({p.species})": (p.id, p.species, p.weight) for p in pets}
pet_label = st.selectbox("반려동물 선택", list(pet_map.keys()))
pet_id, pet_species, pet_base_weight = pet_map[pet_label]

with st.form("daily_form"):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        log_date = st.date_input("기록 날짜", value=date.today())
    with col2:
        weight = st.number_input("몸무게 (kg)", min_value=0.0, step=0.1, format="%.1f")
    with col3:
        food_g = st.number_input("사료량 (g)", min_value=0.0, step=5.0, format="%.1f")
    with col4:
        water_ml = st.number_input("음수량 (ml)", min_value=0.0, step=10.0, format="%.1f")

    activity_min = st.number_input("활동량 (분)", min_value=0.0, step=5.0, format="%.1f")
    notes = st.text_area("메모 (선택)")

    submitted = st.form_submit_button("저장 / 적정량 확인")

if submitted: 
    targets = calc_targets(pet_species, weight)

    food_j = judge(food_g, targets["food_g"])
    water_j = judge(water_ml, targets["water_ml"])
    act_j   = judge(activity_min, targets["activity_min"], 0.9, 1.2)  # 활동은 상한을 좀 더 넓게

    st.info(
        (f"""사료량: **{food_j}** (권장 {targets['food_g']:.0f} g) |
        음수량: **{water_j}** (권장 {targets['water_ml']:.0f} ml) |
        활동량: **{act_j}** (권장 {targets['activity_min']:.0f} 분)""")
    )

    #DB 저장
    with engine.begin() as conn:
        conn.execute(
            text("""
            INSERT INTO daily_logs (user_id, pet_id, log_date, weight, food_g, water_ml, activity_min, notes, updated_at)
            VALUES (:uid, :pid, :d, :w, :f, :wm, :am, :n, CURRENT_TIMESTAMP)
            ON CONFLICT(pet_id, log_date) DO UPDATE SET
              weight=excluded.weight,
              food_g=excluded.food_g,
              water_ml=excluded.water_ml,
              activity_min=excluded.activity_min,
              notes=excluded.notes,
              updated_at=CURRENT_TIMESTAMP
            """),
            {"uid": user_id, "pid": pet_id, "d": log_date.isoformat(),
             "w": float(weight) if weight else None,
             "f": float(food_g) if food_g else None,
             "wm": float(water_ml) if water_ml else None,
             "am": float(activity_min) if activity_min else None,
             "n": notes or None}
        )
    st.success(f"{pet_label} - {log_date.isoformat()} 기록 저장/업데이트 완료")

#최근 몸무게 꺾은선 그래프
with engine.begin() as conn:
    rows = conn.execute(
        text("""
        SELECT log_date, weight
        FROM daily_logs
        WHERE user_id=:uid AND pet_id=:pid
          AND log_date >= date('now','-7 day')
        ORDER BY log_date
        """),
        {"uid": user_id, "pid": pet_id}
    ).fetchall()


st.markdown("----------------")
st.subheader(" 📉 최근 몸무게 변화")
df = pd.DataFrame(rows, columns=["date", "weight"])
if not df.empty:
    df["date"] = pd.to_datetime(df["date"])
    fig, ax=plt.subplots()
    ax.plot(df["date"],df["weight"],marker="o")
    ax.set_xlabel("date")
    ax.set_ylabel("weight (kg)")
    fig.autofmt_xdate()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

    fig.autofmt_xdate(rotation=45)
    st.pyplot(fig, use_container_width=True)
else:
    st.caption("최근 7일간의 몸무게 기록이 없습니다.")



#전체데이터보기
st.markdown("-------------------")
with engine.begin() as conn:
    all_rows = conn.execute(
        text("""
        SELECT log_date, weight, food_g, water_ml, activity_min, notes
        FROM daily_logs
        WHERE user_id = :uid AND pet_id = :pid
        ORDER BY log_date DESC
        """),
        {"uid": user_id, "pid": pet_id}
    ).fetchall()

df_all = pd.DataFrame(
    all_rows, columns=["날짜", "몸무게(kg)", "사료량(g)", "음수량(ml)", "활동량(분)", "메모"]
)

with st.expander("📋 과거 기록 전체 보기"):
    if df_all.empty:
        st.info("아직 저장된 기록이 없습니다.")
    else:
        st.dataframe(df_all, use_container_width=True, hide_index=True)

