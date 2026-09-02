import pandas as pd
import requests
import streamlit as st


# iNaturalist 전문 생물 API 기반 곤충 정보 검색
def fetch_insect_info(query):
    # 1. 생물 분류(Taxa) API 호출 (곤충 강: Insecta - id: 47158)
    inat_url = f"https://api.inaturalist.org/v1/taxa?q={query}&taxon_id=47158&locale=ko"

    try:
        res = requests.get(inat_url, timeout=5)
        if res.status_code != 200:
            return None

        data = res.json()
        results = data.get("results", [])

        if not results:
            return None

        # 가장 적합한 생물 결과 정보 추출
        item = results[0]

        # 한글 이름(preferred_common_name) 또는 기본 이름
        korean_name = item.get("preferred_common_name", item.get("name", query))
        scientific_name = item.get("name", "학명 정보 없음")
        rank = item.get("rank", "생물")

        # 고화질 이미지 URL 추출
        image_url = None
        if item.get("default_photo"):
            image_url = item["default_photo"].get("medium_url") or item[
                "default_photo"
            ].get("square_url")

        # 2. 위키피디아에서 상세 설명 보완 (지명 검색 방지 위해 학명 또는 '곤충' 키워드로 검색)
        wiki_summary = "등록된 상세 생태 설명이 없습니다."
        wiki_url = "https://ko.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": "InsectEncyclopediaApp/1.0 (contact@example.com)"
        }

        # 학명으로 위키피디아 검색 시도 (지명 오검색 완벽 차단)
        wiki_params = {
            "action": "query",
            "format": "json",
            "titles": scientific_name,
            "prop": "extracts",
            "exintro": True,
            "explaintext": True,
            "utf8": 1,
        }

        wiki_res = requests.get(
            wiki_url, params=wiki_params, headers=headers, timeout=5
        )
        if wiki_res.status_code == 200:
            pages = wiki_res.json().get("query", {}).get("pages", {})
            page_info = list(pages.values())[0]
            if "extract" in page_info and page_info["extract"]:
                wiki_summary = page_info["extract"]

        # 만약 학명 검색으로 위키 설명이 없다면 '곤충' 키워드를 붙여 재검색
        if wiki_summary == "등록된 상세 생태 설명이 없습니다.":
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{korean_name} 곤충",
                "utf8": 1,
            }
            s_res = requests.get(
                wiki_url, params=search_params, headers=headers, timeout=5
            )
            if s_res.status_code == 200:
                s_results = s_res.json().get("query", {}).get("search", [])
                if s_results:
                    page_title = s_results[0]["title"]
                    # 행정구역(군, 읍, 면 등) 문서는 제외
                    if not any(
                        location_word in page_title
                        for location_word in ["군", "읍", "면", "특별시", "광역시"]
                    ):
                        d_params = {
                            "action": "query",
                            "format": "json",
                            "titles": page_title,
                            "prop": "extracts",
                            "exintro": True,
                            "explaintext": True,
                            "utf8": 1,
                        }
                        d_res = requests.get(
                            wiki_url,
                            params=d_params,
                            headers=headers,
                            timeout=5,
                        )
                        if d_res.status_code == 200:
                            p_info = list(
                                d_res.json()
                                .get("query", {})
                                .get("pages", {})
                                .values()
                            )[0]
                            wiki_summary = p_info.get("extract", wiki_summary)

        return {
            "korean_name": korean_name,
            "scientific_name": scientific_name,
            "rank": rank,
            "image_url": image_url,
            "summary": wiki_summary,
        }

    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {e}")
        return None


# Streamlit 화면 구성
st.title("🐛 대한민국 곤충 생태 백과")
st.write("곤충 이름을 검색하면 전문 생물 DB에서 정확한 생태 정보, 학명, 실제 사진을 가져옵니다.")

search_query = st.text_input(
    "곤충 이름 검색", placeholder="예: 호랑나비, 장수풍뎅이, 사슴벌레, 매미"
)

st.divider()

if search_query:
    with st.spinner(f"'{search_query}' 곤충 정보를 생물 DB에서 검색 중입니다..."):
        info = fetch_insect_info(search_query)

    if not info:
        st.warning(f"'{search_query}'에 대한 곤충 검색 결과를 찾을 수 없습니다. 정확한 곤충 명칭으로 다시 검색해보세요.")
    else:
        st.subheader(f"🔍 검색 결과: {info['korean_name']}")

        with st.expander(
            f"**{info['korean_name']}** (*{info['scientific_name']}*) 생태 정보",
            expanded=True,
        ):
            img_col, info_col = st.columns([1, 2])

            # 좌측: 곤충 실제 사진
            with img_col:
                if info["image_url"]:
                    st.image(
                        info["image_url"],
                        caption=f"{info['korean_name']} 실제 사진",
                        use_container_width=True,
                    )
                else:
                    st.info("📷 등록된 곤충 대표 사진이 없습니다.")

            # 우측: 학명 및 상세 생태 정보
            with info_col:
                st.markdown(f"### 📌 {info['korean_name']}")
                st.markdown(f"**학명(Scientific Name):** *{info['scientific_name']}*")
                st.markdown(f"**분류:** {info['rank']}")
                st.markdown("---")
                st.markdown("#### 🔬 상세 생태 및 설명")
                st.write(info["summary"])
else:
    st.info("찾고 싶은 곤충 이름을 입력하면 조회가 시작됩니다.")
