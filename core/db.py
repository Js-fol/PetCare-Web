from sqlalchemy import create_engine, text
from pathlib import Path

#DB 파일 경로 설정
DB_PATH = Path(__file__).resolve().parents[1] / "data" / "petcare.db"
engine = create_engine(f"sqlite:///{DB_PATH}", future=True)

#테이블 생성
USERS_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash BLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

PETS_SQL = """
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    species TEXT NOT NULL CHECK(species IN ('dog','cat')),
    breed TEXT,
    birth DATE NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, name)
);
"""

DAILY_SQL = """
CREATE TABLE IF NOT EXISTS daily_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pet_id INTEGER NOT NULL,
    log_date DATE NOT NULL,
    weight REAL,
    food_g REAL,
    water_ml REAL,
    activity_min REAL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE,
    UNIQUE (pet_id, log_date)
    );
    """

EVENTS_SQL = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_date DATE NOT NULL,
    title TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

PHOTOS_SQL = """
CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    file_path TEXT NOT NULL,             
    caption TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""

#인덱스 생성
USERS_EMAIL_INX = """
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
"""

DAILY_USER_INX = """
CREATE INDEX IF NOT EXISTS idx_daily_user ON daily_logs(user_id)
"""
DAILY_PETDATE_INX = """
CREATE INDEX IF NOT EXISTS idx_daily_pet_date ON daily_logs(pet_id, log_date)
"""

PHOTOS_INX="""
CREATE INDEX IF NOT EXISTS idx_photos_user_created ON photos(user_id, created_at DESC);
"""

def init_db():  #db 초기화 함수
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON")) #외래키 활성화로 안정성 확보
        #테이블과 인덱스 생성 함수 호출
        conn.execute(text(USERS_SQL))
        conn.execute(text(USERS_EMAIL_INX))
        conn.execute(text(PETS_SQL))
        conn.execute(text(DAILY_SQL))
        conn.execute(text(DAILY_USER_INX))
        conn.execute(text(DAILY_PETDATE_INX))
        conn.execute(text(EVENTS_SQL))
        conn.execute(text(PHOTOS_SQL))
        conn.execute(text(PHOTOS_INX))