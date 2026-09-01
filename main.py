import sqlite3
import pandas as pd
import streamlit as st


# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect("korea_insects.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            korean_name TEXT NOT NULL,
            habitat TEXT,
            breeding_season TEXT,
            ecology TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()

st.title("한국 곤충 생태 백과")

# 입력 폼 영역
st.subheader("곤충 정보 등록")
with st.form("insect_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        sci_name = st.text_input("학명 *")
        habitat = st.text_input("서식지")
    with col2:
        kor_name = st.text_input("이름(국명) *")
        breeding = st.text_input("번식 시기")

    ecology = st.text_area("생태 특징")
    submitted = st.form_submit_button("정보 등록")

    if submitted:
        if not sci_name or not kor_name:
            st.warning("학명과 이름은 필수 입력 항목입니다.")
        else:
            conn = sqlite3.connect("korea_insects.db")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO insects (scientific_name, korean_name, habitat, breeding_season, ecology)
                VALUES (?, ?, ?, ?, ?)
            """,
                (sci_name, kor_name, habitat, breeding, ecology),
            )
            conn.commit()
            conn.close()
            st.success(f"'{kor_name}' 정보가 등록되었습니다!")

st.divider()

# 검색 및 전체 목록 조회
st.subheader("곤충 목록 및 검색")
search_query = st.text_input("곤충 이름(국명) 검색")

conn = sqlite3.connect("korea_insects.db")
if search_query:
    df = pd.read_sql_query(
        "SELECT scientific_name AS 학명, korean_name AS 이름, habitat AS 서식지, breeding_season AS 번식시기, ecology AS 생태특징 FROM insects WHERE korean_name LIKE ?",
        conn,
        params=(f"%{search_query}%",),
    )
else:
    df = pd.read_sql_query(
        "SELECT scientific_name AS 학명, korean_name AS 이름, habitat AS 서식지, breeding_season AS 번식시기, ecology AS 생태특징 FROM insects",
        conn,
    )
conn.close()

st.dataframe(df, use_container_width=True)
