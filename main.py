import sqlite3
import pandas as pd
import streamlit as st


# 데이터베이스 초기화 및 컬럼 자동 업데이트
def init_db():
    conn = sqlite3.connect("korea_insects.db")
    cursor = conn.cursor()

    # 1. 기본 테이블 생성 (없을 경우)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS insects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scientific_name TEXT NOT NULL,
            korean_name TEXT NOT NULL,
            habitat TEXT,
            breeding_season TEXT,
            diet TEXT,
            activity_time TEXT,
            ecology TEXT,
            image_url TEXT
        )
    """)

    # 2. 기존 테이블에 누락된 컬럼이 있다면 자동으로 추가 (기존 DB 호환용)
    cursor.execute("PRAGMA table_info(insects)")
    existing_columns = [col[1] for col in cursor.fetchall()]

    new_columns = {
        "diet": "TEXT",
        "activity_time": "TEXT",
        "image_url": "TEXT",
    }

    for col_name, col_type in new_columns.items():
        if col_name not in existing_columns:
            cursor.execute(f"ALTER TABLE insects ADD COLUMN {col_name} {col_type}")

    # 3. 데이터가 비어있을 경우 테스트용 샘플 데이터 입력
    cursor.execute("SELECT COUNT(*) FROM insects")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            (
                "Lucanus maculifemoratus",
                "사슴벌레",
                "참나무 숲, 온대 활엽수림",
                "6월 ~ 8월",
                "참나무, 버드나무 등의 발효 수액",
                "야행성 (해질녘부터 새벽까지 활동)",
                "수컷은 커다란 턱을 이용해 영역 싸움을 벌이며, 빛에 끌리는 주광성이 강해 밤에 인가나 등불 근처로 날아오기도 합니다. 유충 기간은 약 1~2년으로 부엽토나 썩은 나무 속에서 성장합니다.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d0/Lucanus_maculifemoratus_maculifemoratus_Male_A.jpg/640px-Lucanus_maculifemoratus_maculifemoratus_Male_A.jpg",
            ),
            (
                "Allomyrina dichotoma",
                "장수풍뎅이",
                "활엽수림, 참나무 군락지",
                "7월 ~ 8월",
                "참나무 수액, 과일 즙",
                "야행성",
                "한국 곤충 중 가장 힘이 세며, 수컷 머리에 있는 Y자 모양의 커다란 뿔로 다른 수컷을 밀어내며 나무 수액을 차지합니다. 성충의 수명은 1~3개월 정도로 짧은 편입니다.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/3/36/Allomyrina_dichotoma_septentrionalis_Male.jpg/640px-Allomyrina_dichotoma_septentrionalis_Male.jpg",
            ),
            (
                "Apatura iris",
                "오색나비",
                "산지 숲길, 계곡 주변",
                "5월 ~ 9월",
                "나무 수액, 썩은 과일, 동물의 사체나 분변",
                "주행성 (낮 시간대)",
                "수컷의 날개 표면은 보는 각도에 따라 강렬한 보라색 구조색 광택을 띱니다. 높은 나무 위에서 영역을 지키는 습성이 있으며, 꽃의 꿀보다는 수액이나 습한 땅바닥의 미네랄을 주로 섭취합니다.",
                "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Apatura_iris_male_side.jpg/640px-Apatura_iris_male_side.jpg",
            ),
        ]
        cursor.executemany(
            """
            INSERT INTO insects (
                scientific_name, korean_name, habitat, breeding_season, 
                diet, activity_time, ecology, image_url
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            sample_data,
        )

    conn.commit()
    conn.close()


# 데이터베이스 초기화
init_db()

# 화면 기본 설정
st.title("🐛 한국 곤충 생태 백과")
st.write("찾고 싶은 곤충의 이름을 입력하여 자세한 생태 정보와 학명, 사진을 확인해보세요.")

# 검색창 영역
search_query = st.text_input(
    "곤충 이름(국명) 검색", placeholder="예: 사슴벌레, 장수풍뎅이"
)

st.divider()

# 데이터베이스 연결 및 조회
conn = sqlite3.connect("korea_insects.db")

if search_query:
    df = pd.read_sql_query(
        """SELECT scientific_name, korean_name, habitat, breeding_season, 
                  diet, activity_time, ecology, image_url 
           FROM insects WHERE korean_name LIKE ?""",
        conn,
        params=(f"%{search_query}%",),
    )
else:
    df = pd.read_sql_query(
        """SELECT scientific_name, korean_name, habitat, breeding_season, 
                  diet, activity_time, ecology, image_url 
           FROM insects""",
        conn,
    )

conn.close()

# 검색 결과 보여주기
if df.empty:
    st.info(f"'{search_query}'에 대한 검색 결과가 없습니다.")
else:
    st.subheader(f"검색 결과 (총 {len(df)}건)")

    for idx, row in df.iterrows():
        with st.expander(
            f"**{row['korean_name']}** (*{row['scientific_name']}*)", expanded=True
        ):
            img_col, info_col = st.columns([1, 2])

            # 좌측: 사진 영역
            with img_col:
                if row["image_url"]:
                    st.image(
                        row["image_url"],
                        caption=f"{row['korean_name']}",
                        use_container_width=True,
                    )
                else:
                    st.write("📷 등록된 사진이 없습니다.")

            # 우측: 정보 영역
            with info_col:
                st.markdown(f"### 📌 {row['korean_name']}")
                st.markdown(f"**학명:** *{row['scientific_name']}*")

                st.markdown("---")
                st.markdown(f"- **서식 환경:** {row['habitat'] or '정보 없음'}")
                st.markdown(f"- **활동/번식 시기:** {row['breeding_season'] or '정보 없음'}")
                st.markdown(f"- **주 먹이:** {row['diet'] or '정보 없음'}")
                st.markdown(f"- **활동 시간:** {row['activity_time'] or '정보 없음'}")

            # 하단: 세부 생태 습성 및 특징
            st.markdown("---")
            st.markdown("#### 🔬 상세 생태 및 습성")
            st.info(row["ecology"] or "등록된 상세 생태 정보가 없습니다.")
