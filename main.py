import pandas as pd
import requests
import streamlit as st


# iNaturalist + 위키백과 전문 정보를 활용한 상세 곤충 검색 (한국 자생종 + 상세 생태)
def fetch_insect_info(query):
    try:
        # 1. 대한민국(place_id=6857) 내 관찰된 곤충(taxon_id=47158) 검색
        search_url = f"https://api.inaturalist.org/v1/observations?q={query}&taxon_id=47158&place_id=6857&per_page=1&locale=ko"
        res = requests.get(search_url, timeout=5)

        if res.status_code != 200:
            return None

        data = res.json()
        results = data.get("results", [])

        # 한국 내 관찰 기록이 없는 경우 차단
        if not results:
            return None

        # 관찰 기록에서 곤충 분류(Taxon) 상세 정보 추출
        obs = results[0]
        taxon = obs.get("taxon", {})
        taxon_id = taxon.get("id")

        if not taxon_id:
            return None

        korean_name = taxon.get(
            "preferred_common_name", taxon.get("name", query)
        )
        scientific_name = taxon.get("name", "학명 정보 없음")
        rank = taxon.get("rank", "곤충")

        # --- [추가] 상세 분류 계통 (목, 과 정보 추출) ---
        ancestors = taxon.get("ancestors", [])
        order_name = "미정"
        family_name = "미정"

        for anc in ancestors:
            anc_rank = anc.get("rank")
            if anc_rank == "order":
                order_name = anc.get(
                    "preferred_common_name", anc.get("name", "미정")
                )
            elif anc_rank == "family":
                family_name = anc.get(
                    "preferred_common_name", anc.get("name", "미정")
                )

        # --- [추가] 보전 상태 (멸종위기/보호종 등) ---
        conservation_status = "관심대상(LC) / 일반종"
        cs_info = taxon.get("conservation_status")
        if cs_info:
            conservation_status = cs_info.get(
                "status_name", cs_info.get("status", "보호종 지정")
            )

        # --- 한국 관찰 사진 추출 ---
        image_url = None
        if obs.get("photos"):
            photo_info = obs["photos"][0]
            image_url = photo_info.get("url", "").replace("square", "medium")

        if not image_url and taxon.get("default_photo"):
            image_url = taxon["default_photo"].get("medium_url") or taxon[
                "default_photo"
            ].get("square_url")

        # --- 한국 내 누적 관찰 수 및 활동 시기 추출 ---
        korea_stats_url = f"https://api.inaturalist.org/v1/observations?taxon_id={taxon_id}&place_id=6857&per_page=0"
        stats_res = requests.get(korea_stats_url, timeout=5)
        observations_count = 0
        if stats_res.status_code == 200:
            observations_count = stats_res.json().get("total_results", 0)

        # 한국 내 월별 활동 히스토그램
        histogram_url = f"https://api.inaturalist.org/v1/observations/histogram?taxon_id={taxon_id}&place_id=6857&date_field=observed"
        histo_res = requests.get(histogram_url, timeout=5)

        active_months = []
        if histo_res.status_code == 200:
            month_data = (
                histo_res.json().get("results", {}).get("month_of_year", {})
            )
            sorted_months = sorted(
                month_data.items(), key=lambda x: x[1], reverse=True
            )
            active_months = [
                f"{m[0]}월" for m in sorted_months[:4] if m[1] > 0
            ]

        # 2. 위키백과 상세 정보 검색 (전문 생태 설명 추출 강화)
        wiki_summary = ""
        wiki_url = "https://ko.wikipedia.org/w/api.php"
        headers = {
            "User-Agent": "InsectEncyclopediaApp/1.0 (contact@example.com)"
        }

        # 학명 및 국명으로 위키백과 본문 검색
        wiki_params = {
            "action": "query",
            "format": "json",
            "titles": f"{korean_name}|{scientific_name}",
            "prop": "extracts",
            "explaintext": True,
            "utf8": 1,
        }

        wiki_res = requests.get(
            wiki_url, params=wiki_params, headers=headers, timeout=5
        )
        if wiki_res.status_code == 200:
            pages = wiki_res.json().get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if page_id != "-1" and "extract" in page_info:
                    wiki_summary = page_info["extract"]
                    break

        if not wiki_summary or len(wiki_summary) < 50:
            search_params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"{korean_name} 생태",
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
            wiki_summary = (
                f"{korean_name}(학명: {scientific_name})은(는) {order_name} {family_name}에 속하는 대한민국 자생 곤충입니다.\n\n"
                f"• **서식 환경:** 주로 {active_months[0] if active_months else '여름철'} 국내 산지, 숲, 하천 변 등 다양한 자연환경에서 주로 관찰됩니다.\n"
                f"• **생태적 특징:** 한국 자연 생태계의 주요 먹이사슬 구성원이며, 성충과 애벌레 시기에 따라 다양한 생태적 역할을 수행합니다."
            )

        return {
            "korean_name": korean_name,
            "scientific_name": scientific_name,
            "rank": rank,
            "order_name": order_name,
            "family_name": family_name,
            "conservation_status": conservation_status,
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
st.title("🐛 대한민국 자생 곤충 상세 생태 백과")
st.write(
    "곤충 이름을 검색하면 생물 분류, 보전 등급, 국내 관찰 사진, 상세 생태 설명을 보여줍니다."
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
            f"'{search_query}'에 대한 국내 서식 곤충 검색 결과를 찾을 수 없습니다."
        )
    else:
        st.subheader(f"🔍 검색 결과: {info['korean_name']}")

        with st.expander(
            f"**{info['korean_name']}** (*{info['scientific_name']}*) 상세 생태 정보",
            expanded=True,
        ):
            img_col, info_col = st.columns([1, 2])

            # 좌측: 곤충 실제 사진
            with img_col:
                if info["image_url"]:
                    st.image(
                        info["image_url"],
                        caption=f"{info['korean_name']} 국내 관찰 사진",
                        use_container_width=True,
                    )
                else:
                    st.info("📷 등록된 국내 사진이 없습니다.")

            # 우측: 상세 분류 및 생태 정보
            with info_col:
                st.markdown(f"### 📌 {info['korean_name']}")
                st.markdown(
                    f"**학명(Scientific Name):** *{info['scientific_name']}*"
                )
                st.markdown(
                    f"**생물 분류:** {info['order_name']} (Order) > {info['family_name']} (Family)"
                )
                st.markdown(
                    f"**보전 상태:** `{info['conservation_status']}`"
                )

                # --- 곤충 생태 요약 정보 지표 ---
                st.markdown("---")
                st.markdown("#### 🌿 국내 관찰 생태 요약")
                st.write(
                    f"• **주요 관찰/활동 시기:** {info['active_months']}"
                )
                st.write(
                    f"• **국내 누적 관찰 기록:** {info['observations_count']:,}회"
                )

            # 하단: 상세 생태 및 백과 설명
            st.markdown("---")
            st.markdown("#### 🔬 상세 생태 특징 및 백과 설명")

            paragraphs = info["summary"].split("\n")
            for p in paragraphs:
                if p.strip():
                    st.write(p.strip())

else:
    st.info("찾고 싶은 곤충 이름을 입력하면 상세 생태 조회가 시작됩니다.")
