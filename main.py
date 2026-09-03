import pandas as pd
import requests
import streamlit as st


# iNaturalist + 위키백과 전문 정보를 활용한 상세 곤충 검색
def fetch_insect_info(query):
    # 1. iNaturalist 생물 분류 API (곤충 강: taxon_id=47158)
    inat_url = (
        f"https://api.inaturalist.org/v1/taxa?q={query}&taxon_id=47158&locale=ko"
    )

    try:
        res = requests.get(inat_url, timeout=5)
        if res.status_code != 200:
            return None

        data = res.json()
        results = data.get("results", [])

        if not results:
            return None

        # 가장 적합한 곤충 데이터 추출
        item = results[0]
        taxon_id = item.get("id")
        korean_name = item.get("preferred_common_name", item.get("name", query))
        scientific_name = item.get("name", "학명 정보 없음")
        rank = item.get("rank", "곤충")

        # 고화질 이미지 URL 추출
        image_url = None
        if item.get("default_photo"):
            image_url = item["default_photo"].get("medium_url") or item[
                "default_photo"
            ].get("square_url")

        # --- [추가] 1-1. iNaturalist 관찰 기반 생태 데이터 추출 (월별 활동 및 관찰 수) ---
        observations_count = item.get("observations_count", 0)

        # 월별 활동 데이터를 가져오기 위한 추가 API 요청
        histogram_url = f"https://api.inaturalist.org/v1/observations/histogram?taxon_id={taxon_id}&date_field=observed"
        histo_res = requests.get(histogram_url, timeout=5)

        active_months = []
        if histo_res.status_code == 200:
            month_data = (
                histo_res.json().get("results", {}).get("month_of_year", {})
            )
            # 가장 많이 관찰되는 Top 3 월 추출
            sorted_months = sorted(
                month_data.items(), key=lambda x: x[1], reverse=True
            )
            active_months = [
                f"{m[0]}월" for m in sorted_months[:4] if m[1] > 0
            ]

        # 2. 위키백과 상세 정보 검색
        wiki_summary = ""
        wiki_url = "https://ko.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": "InsectEncyclopediaApp/1.0 (contact@example.com)"
        }

        wiki_params = {
            "action": "query",
            "format": "json",
            "titles": scientific_name,
            "prop": "extracts",
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

        if not wiki_summary or len(wiki_summary) < 50:
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
                    if not any(
                        location_word in page_title
                        for location_word in ["군", "읍", "면", "특별시", "광역시"]
                    ):
                        d_params = {
                            "action": "query",
                            "format": "json",
                            "titles": page_title,
                            "prop": "extracts",
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
                            wiki_summary = p_info.get(
                                "extract", wiki_summary
                            )

        if not wiki_summary:
            wiki_summary = f"{korean_name}(학명: {scientific_name})에 대한 개요 정보입니다. 해당 종은 {rank} 분류군에 속하며 자세한 생태 백과 내용이 지속적으로 업데이트 중입니다."

        return {
            "korean_name": korean_name,
            "scientific_name": scientific_name,
            "rank": rank,
            "image_url": image_url,
            "summary": wiki_summary,
            "observations_count": observations_count,
            "active_months": (
                ", ".join(active_months)
                if active_months
                else "데이터 준비 중"
            ),
        }

    except Exception as e:
        st.error(f"데이터 조회 중 오류 발생: {e}")
        return None


# Streamlit 화면 구성
st.title("🐛 대한민국 곤충 생태 백과")
st.write(
    "곤충 이름을 검색하면 학명, 사진, 상세 생태 설명을 종합적으로 보여줍니다."
)

search_query = st.text_input(
    "곤충 이름 검색", placeholder="예: 호랑나비, 장수풍뎅이, 사슴벌레, 매미, 무당벌레"
)

st.divider()

if search_query:
    with st.spinner(
        f"'{search_query}'의 상세 생태 정보를 불러오는 중입니다..."
    ):
        info = fetch_insect_info(search_query)

    if not info:
        st.warning(
            f"'{search_query}'에 대한 곤충 검색 결과를 찾을 수 없습니다. 정확한 곤충 이름으로 다시 검색해보세요."
        )
    else:
        st.subheader(f"🔍 검색 결과: {info['korean_name']}")

        with st.expander(
            f"**{info['korean_name']}** (*{info['scientific_name']}*) 상세 생태 백과",
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

            # 우측: 학명 및 기본 생태 정보
            with info_col:
                st.markdown(f"### 📌 {info['korean_name']}")
                st.markdown(
                    f"**학명(Scientific Name):** *{info['scientific_name']}*"
                )
                st.markdown(f"**생물 분류:** {info['rank']}")

                # --- [추가] 곤충 생태 요약 정보 지표 ---
                st.markdown("---")
                st.markdown("#### 🌿 곤충 생태 요약")
                st.write(
                    f"• **주요 관찰/활동 시기:** {info['active_months']}"
                )
                st.write(
                    f"• **전 세계 누적 관찰 기록:** {info['observations_count']:,}회"
                )

            # 하단: 전체 상세 생태 및 설명
            st.markdown("---")
            st.markdown("#### 🔬 상세 생태 특징 및 백과 설명")

            paragraphs = info["summary"].split("\n")
            for p in paragraphs:
                if p.strip():
                    st.write(p.strip())

else:
    st.info("찾고 싶은 곤충 이름을 입력하면 상세 생태 조회가 시작됩니다.")
