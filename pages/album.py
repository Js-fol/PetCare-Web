import streamlit as st
from sqlalchemy import text
from pathlib import Path
from datetime import datetime
import uuid
import os
from PIL import Image, ImageOps
from core.db import engine, init_db


init_db()
 #로그인 상태 확인
SESSION_KEY="auth_user"
user=st.session_state.get(SESSION_KEY)
if not user:
    st.warning("로그인이 필요합니다.")
    st.page_link("pages/login.py",label="로그인 페이지로 이동")
    st.stop
user_id=user["id"]

st.title("📷  포토 앨범  😍")
st.caption("반려동물과의 소중한 순간을 기록해보세요!")

#사진 업로드 준비
UPLOAD_DIR=Path("assets/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

#업로드 기능 화면
with st.expander("사진/영상 업로드 하기"):
    with st.form("업로드",clear_on_submit=True):
        files=st.file_uploader("사진/영상 선택 (복수 선택 가능)",type=[".png",".jpg",".jpeg",".mp4",".mov",".avi"], accept_multiple_files=True)
        caption=st.text_input("메모 (선택)")
        submitted=st.form_submit_button("업로드")

        if submitted:
            if not files:
                st.warning("사진/영상을 선택해주세요")
            else:
                with engine.begin() as conn:
                    for f in files:
                        ext=os.path.splitext(f.name)[1].lower()  #안전한 고유 파일명 생성
                        if ext not in [".png",".jpg",".jpeg",".mp4",".mov",".avi"]:
                            continue
                        fname=(f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}")
                        save_path = UPLOAD_DIR / fname

                        save_path.write_bytes(f.getbuffer())  #파일 저장
                        rel_path=str(save_path.as_posix())  #db저장
                        conn.execute(text ("""
                                        INSERT INTO photos (user_id, file_path,caption)
                                        VALUES (:uid, :path,:cap)
                                        """),
                                        {"uid":user_id,"path":rel_path,"cap":caption.strip() or None})
                    st.success(f"업로드 완료")
                
st.markdown("---")

#사진 표시
with engine.begin() as conn:
    rows=conn.execute(text("""
                            SELECT id, file_path, caption, created_at
                            FROM photos
                            WHERE user_id = :uid
                            ORDER BY created_at DESC, id DESC
                            """),
                            {"uid": user_id}).fetchall()


if not rows:
    st.info("사진을 업로드해보세요.")

for i in range(0,len(rows),3):
    cols=st.columns(3)
    for j, col in enumerate(cols):
        k=i+j
        if k>=len(rows):
            break
        pid,path,cap,created=rows[k]
        ext = os.path.splitext(path)[1].lower()



        if not Path(path).exists():
            with engine.begin() as conn:
                conn.execute(text("DELETE FROM photos WHERE id=:id AND user_id=:uid"),
                                    {"id":pid, "uid":user_id})
                continue

        img_exts = [".png", ".jpg", ".jpeg"]
        video_exts = [".mp4", ".mov", ".avi"]


        with col:
            if ext in img_exts:
                img=Image.open(Path(path))
                img=ImageOps.exif_transpose(img)  #사진 방향 보정
                st.image(img, use_container_width=True)
            elif ext in video_exts:
                st.video(str(Path(path)))
            if cap:
                st.caption(cap)
            del_btn=st.button("삭제", key=f"del_{pid}")
            if del_btn:
                try:
                    Path(path).unlink(missing_ok=True)
                    st.rerun()
                except Exception:
                    pass
                with engine.begin() as conn:
                    conn.execute(text("DELETE FROM photos WHERE id=:id AND user_id=:uid"),
                                      {"id":pid, "uid":user_id})
                

    
