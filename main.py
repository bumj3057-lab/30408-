import pandas as pd
import requests
import streamlit as st


# 곤충 전용 정보 검색 함수 (위키피디아 + iNaturalist API)
def fetch_insect_info(query):
    headers = {
        "User-Agent": "InsectEncyclopediaApp/1.0 (contact@example.com)"
    }

    # 1. '곤충' 키워드를 명시하여 검색 (영양군 같은 지명 검색 방지)
    search_query = f"{query} 곤충" if not query.endswith("곤충") else query
    search_url = "https://ko.wikipedia.org/w/api.php"

    search_params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": search_query,
        "utf8": 1,
    }

    try:
        res = requests.get(
            search_url, params=search_params, headers=headers, timeout=5
        )

        if res.status_code != 200:
            return None

        data = res.json()
        search_results = data.get("query", {}).get("search", [])

        if not search_results:
            # '곤충' 키워드 없이 재검색
            search_params["srsearch"] = query
            res = requests.get(
                search_url, params=search_params, headers=headers, timeout=5
            )
            data = res.json()
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                return None

        # 가장 적합한 문서 선택
        page_title = search_results[0]["title"]

        # 2. 상세 본문 및 이미지 정보 추출
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

        # 3. 만약 위키피디아에 이미지가 없으면 iNaturalist 생물 API에서 실제 사진 추가 검색
        if not image_url:
            inat_url = f"https://api.inaturalist.org/v1/taxa?q={query}&locale=ko"
            inat_res = requests.get(inat_url, timeout=3)
            if inat_res.status_code == 200:
                inat_data = inat_res.json()
                results = inat_data.get("results", [])
                if results and results[0].get("default_photo"):
                    image_url = results[0]["default_photo"].get("medium_url")

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
st.write("곤충 이름을 검색하면 실시간 생태 정보, 사진, 특징을 조회합니다.")

search_query = st.text_input(
    "곤충 이름 검색", placeholder="예: 호랑나비, 장수풍뎅이, 사슴벌레, 무당벌레"
)

st.divider()

if search_query:
    with st.spinner(f"'{search_query}' 곤충 정보를 검색 중입니다..."):
        info = fetch_insect_info(search_query)

    if not info:
        st.warning(f"'{search_query}'에 대한 곤충 검색 결과를 찾을 수 없습니다. 정확한 곤충 명칭으로 검색해보세요.")
    else:
        st.subheader(f"🔍 검색 결과: {info['title']}")

        with st.expander(f"**{info['title']}** 생태 상세 정보", expanded=True):
            img_col, info_col = st.columns([1, 2])

            # 좌측: 곤충 사진
            with img_col:
                if info["image_url"]:
                    st.image(
                        info["image_url"],
                        caption=f"{info['title']} 실제 사진",
                        use_container_width=True,
                    )
                else:
                    st.info("📷 등록된 곤충 대표 이미지 사진이 없습니다.")

            # 우측: 생태 및 정보
            with info_col:
                st.markdown(f"### 📌 {info['title']}")
                st.markdown("---")
                st.markdown("#### 🔬 생태 특징 및 개요")
                st.write(info["summary"])
else:
    st.info("찾고 싶은 곤충 이름을 입력하면 조회가 시작됩니다.")
