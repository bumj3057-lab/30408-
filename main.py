import pandas as pd
import requests
import streamlit as st


# 위키피디아 및 Open API를 통한 곤충 정보 검색
def fetch_insect_info(query):
    # 위키피디아 차단을 방지하기 위한 User-Agent 설정
    headers = {
        "User-Agent": "InsectEncyclopediaApp/1.0 (contact@example.com)"
    }
    search_url = "https://ko.wikipedia.org/w/api.php"

    # 1. 위키피디아 검색 API 호출
    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "utf8": 1,
    }

    try:
        res = requests.get(
            search_url, params=search_params, headers=headers, timeout=5
        )

        # 응답 상태 확인
        if res.status_code != 200:
            return None

        data = res.json()
        search_results = data.get("query", {}).get("search", [])

        if not search_results:
            return None

        # 가장 연관성이 높은 문서 제목 추출
        page_title = search_results[0]["title"]

        # 2. 상세 정보 및 대표 이미지 URL 추출
        detail_params = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "extracts|pageimages",
            "exintro": True,
            "explaintext": True,
            "piprop": "original",
            "utf8": 1,
        }

        detail_res = requests.get(
            search_url, params=detail_params, headers=headers, timeout=5
        )
        if detail_res.status_code != 200:
            return None

        detail_data = detail_res.json()
        pages = detail_data.get("query", {}).get("pages", {})

        page_info = list(pages.values())[0]

        summary = page_info.get("extract", "상세 생태 정보가 제공되지 않습니다.")
        image_url = page_info.get("original", {}).get("source", None)

        return {
            "title": page_title,
            "summary": summary,
            "image_url": image_url,
        }

    except Exception as e:
        st.error(f"데이터 처리 중 오류 발생: {e}")
        return None


# Streamlit 화면 구성
st.title("🐛 대한민국 곤충 생태 백과")
st.write("한국에 서식하는 곤충 이름을 검색하면 실시간 생태 정보, 학명, 사진을 가져옵니다.")

search_query = st.text_input(
    "곤충 이름 검색", placeholder="예: 호랑나비, 장수풍뎅이, 매미, 무당벌레"
)

st.divider()

if search_query:
    with st.spinner(f"'{search_query}' 정보를 검색 중입니다..."):
        info = fetch_insect_info(search_query)

    if not info:
        st.warning(f"'{search_query}'에 대한 검색 결과를 찾을 수 없습니다. 정확한 곤충 이름으로 다시 검색해보세요.")
    else:
        st.subheader(f"검색 결과: {info['title']}")

        with st.expander(f"**{info['title']}** 생태 정보 보기", expanded=True):
            img_col, info_col = st.columns([1, 2])

            # 사진 영역
            with img_col:
                if info["image_url"]:
                    st.image(
                        info["image_url"],
                        caption=f"{info['title']} 실제 사진",
                        use_container_width=True,
                    )
                else:
                    st.info("📷 등록된 대표 이미지 사진이 없습니다.")

            # 상세 설명 영역
            with info_col:
                st.markdown(f"### 📌 {info['title']}")
                st.markdown("---")
                st.markdown("#### 🔬 상세 생태 및 설명")
                st.write(
                    info["summary"][:500]
                    + ("..." if len(info["summary"]) > 500 else "")
                )
else:
    st.info("검색어를 입력하고 Enter를 누르면 정보 조회가 시작됩니다.")
