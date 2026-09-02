import sqlite3
import pandas as pd
import streamlit as st


# 데이터베이스 초기화 및 기본 샘플 데이터 입력
def init_db():
    conn = sqlite3.connect("korea_insects.db")
    cursor = conn.cursor()

    # 이미지 URL(image_url) 컬럼 추가
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            korean_name TEXT NOT NULL,
            habitat TEXT,
            breeding_season TEXT,
            ecology TEXT,
            image_url TEXT
        )
    """)

    # 테이블이 비어있을 경우 테스트용 기본 데이터 추가
    cursor.execute("SELECT COUNT(*) FROM insects")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            (
                "Lucanus maculifemoratus",
                "사슴벌레",
                "참나무 숲",
                "6월 ~ 8월",
                "야행성이며 참나무 즙을 먹고 산다.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Lucanus_maculifemoratus_maculifemoratus_Male_A.jpg/640px-Lucanus_maculifemoratus_maculifemoratus_Male_A.jpg",
            ),
            (
                "Allomyrina dichotoma",
                "장수풍뎅이",
                "활엽수림",
                "7월 ~ 8월",
                "힘이 세고 활엽수의 수액을 주로 먹는다.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Allomyrina_dichotoma_septentrionalis_Male.jpg/640px-Allomyrina_dichotoma_septentrionalis_Male.jpg",
            ),
            (
                "Apatura iris",
                "오색나비",
                "산지 숲길",
                "5월 ~ 9월",
                "날개에 아름다운 보라색 광택이 난다.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Apatura_iris_male_side.jpg/640px-Apatura_iris_male_side.jpg",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO insects (scientific_name, korean_name, habitat, breeding_season, ecology, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            sample_data,
        )

    conn.commit()
    conn.close()


init_db()

# 화면 기본 설정
st.title("🐛 한국 곤충 생태 백과")
st.write("찾고 싶은 곤충의 이름을 입력하여 생태 정보와 학명, 사진을 확인해보세요.")

# 검색창 영역
search_query = st.text_input(
    "곤충 이름(국명) 검색", placeholder="예: 사슴벌레, 장수풍뎅이"
)

st.divider()

# 데이터베이스 연결 및 조회
conn = sqlite3.connect("korea_insects.db")

if search_query:
    # 검색어가 있을 경우 조건 조회
    df = pd.read_sql_query(
        "SELECT scientific_name, korean_name, habitat, breeding_season, ecology, image_url FROM insects WHERE korean_name LIKE ?",
        conn,
        params=(f"%{search_query}%",),
    )
else:
    # 검색어가 없을 경우 전체 데이터 조회
    df = pd.read_sql_query(
        "SELECT scientific_name, korean_name, habitat, breeding_season, ecology, image_url FROM insects",
        conn,
    )

conn.close()

# 검색 결과 보여주기
if df.empty:
    st.info(f"'{search_query}'에 대한 검색 결과가 없습니다.")
else:
    st.subheader(f"검색 결과 (총 {len(df)}건)")

    for idx, row in df.iterrows():
        # 카드 형태로 정보 출력
        with st.expander(
            f"**{row['korean_name']}** (*{row['scientific_name']}*)", expanded=True
        ):
            img_col, info_col = st.columns([1, 2])

            # 좌측: 사진 영역
            with img_col:
                if row["image_url"]:
                    st.image(
                        row["image_url"],
                        caption=f"{row['korean_name']} 사진",
                        use_container_width=True,
                    )
                else:
                    st.write("📷 등록된 사진이 없습니다.")

            # 우측: 정보 영역
            with info_col:
                st.markdown(f"**학명:** *{row['scientific_name']}*")
                st.markdown(f"**서식지:** {row['habitat'] or '정보 없음'}")
                st.markdown(f"**번식 시기:** {row['breeding_season'] or '정보 없음'}")
                st.markdown("**생태 특징:**")
                st.write(row["ecology"] or "정보 없음")
