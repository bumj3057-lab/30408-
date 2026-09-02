import pandas as pd
import requests
import streamlit as st

# 국립생물자원관 또는 공공데이터포럼에서 발급받은 API KEY
API_KEY = "YOUR_API_KEY_HERE"


# 외부 API를 통해 곤충 정보 및 이미지 가져오기
def search_insect_api(query):
    # 실제 사용할 공공 API 엔드포인트 URL
    url = f"http://apis.data.go.kr/1400119/InsectService/getInsectDetailSearch?serviceKey={API_KEY}&q1={query}"

    try:
        response = requests.get(url, timeout=5)
        # API 응답 파싱 (API 제공 형식이 XML인지 JSON인지에 따라 파싱 방식 조정 필요)
        if response.status_code == 200:
            # 예시 구조 (실제 API 응답 데이터에 맞게 필드명 매핑)
            data = response.json()
            return data.get("items", [])
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return []


# 화면 기본 설정
st.title("🐛 대한민국 곤충 생태 백과 (전종 검색)")
st.write(
    "국가 생물 종 목록 API와 연동되어 한국의 모든 곤충을 검색할 수 있습니다."
)

search_query = st.text_input(
    "곤충 이름(국명 또는 학명) 검색", placeholder="예: 장수풍뎅이, 호랑나비, 매미"
)

st.divider()

if search_query:
    with st.spinner("국가 데이터베이스에서 곤충 정보를 검색 중입니다..."):
        # API 호출
        results = search_insect_api(search_query)

    if not results:
        st.info(f"'{search_query}'에 대한 검색 결과가 없습니다.")
    else:
        st.subheader(f"검색 결과 (총 {len(results)}건)")

        for item in results:
            korean_name = item.get("koreanName", "정보 없음")
            scientific_name = item.get("scientificName", "정보 없음")
            image_url = item.get("imageUrl", "")
            habitat = item.get("habitat", "정보 없음")
            ecology = item.get("description", "정보 없음")

            with st.expander(
                f"**{korean_name}** (*{scientific_name}*)", expanded=True
            ):
                img_col, info_col = st.columns([1, 2])

                with img_col:
                    if image_url:
                        st.image(
                            image_url,
                            caption=korean_name,
                            use_container_width=True,
                        )
                    else:
                        st.write("📷 등록된 사진이 없습니다.")

                with info_col:
                    st.markdown(f"### 📌 {korean_name}")
                    st.markdown(f"**학명:** *{scientific_name}*")
                    st.markdown("---")
                    st.markdown(f"- **서식 환경:** {habitat}")

                st.markdown("---")
                st.markdown("#### 🔬 상세 생태 및 습성")
                st.info(ecology)
else:
    st.write("검색어를 입력하시면 전체 국가 곤충 DB에서 정보가 조회됩니다.")
