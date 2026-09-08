import pandas as pd
import requests
import streamlit as st


def fetch_insect_info(query):
    try:
        headers = {
            "User-Agent": "InsectEncyclopediaApp/1.0 (contact@example.com)"
        }

        # 1. Taxa Search API로 곤충 분류군 우선 검색 (성공률 향상)
        taxon_url = f"https://api.inaturalist.org/v1/taxa?q={query}&taxon_id=47158&locale=ko"
        t_res = requests.get(taxon_url, headers=headers, timeout=8)

        if t_res.status_code != 200:
            return None

        t_data = t_res.json()
        t_results = t_data.get("results", [])

        if not t_results:
            return None

        # 가장 검색 연관도가 높은 분류군 선택
        taxon = t_results[0]
        taxon_id = taxon.get("id")

        korean_name = taxon.get(
            "preferred_common_name", taxon.get("name", query)
        )
        scientific_name = taxon.get("name", "학명 정보 없음")
        rank = taxon.get("rank", "곤충")

        # 분류 계통 추출 (목, 과)
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

        # 보전 상태
        conservation_status = "관심대상(LC) / 일반종"
        cs_info = taxon.get("conservation_status")
        if cs_info:
            conservation_status = cs_info.get(
                "status_name", cs_info.get("status", "보호종 지정")
            )

        # 기본 대표 이미지 확보
        image_url = None
        if taxon.get("default_photo"):
            image_url = taxon["default_photo"].get("medium_url") or taxon[
                "default_photo"
            ].get("square_url")

        # 2. 한국 내 관찰 기록 및 국내 대표 이미지 조회
        obs_url = f"https://api.inaturalist.org/v1/observations?taxon_id={taxon_id}&place_id=6857&per_page=1&locale=ko"
        obs_res = requests.get(obs_url, headers=headers, timeout=8)
        observations_count = 0

        if obs_res.status_code == 200:
            obs_data = obs_res.json()
            observations_count = obs_data.get("total_results", 0)
            obs_results = obs_data.get("results", [])

            # 한국 내 관찰 사진이 있다면 우선 사용
            if obs_results and obs_results[0].get("photos"):
                photo_info = obs_results[0]["photos"][0]
                image_url = photo_info.get("url", "").replace(
                    "square", "medium"
                )

        # 월별 활동 히스토그램
        histogram_url = f"https://api.inaturalist.org/v1/observations/histogram?taxon_id={taxon_id}&place_id=6857&date_field=observed"
        histo_res = requests.get(histogram_url, headers=headers, timeout=8)

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

        # 3. 위키백과 상세 정보 검색
        wiki_summary = ""
        wiki_url = "https://ko.wikipedia.org/w/api.php"

        # 검색어 후보군 (국명, 검색 입력값, 학명)
        search_terms = list(
            dict.fromkeys([korean_name, query, scientific_name])
        )

        for term in search_terms:
            wiki_params = {
                "action": "query",
                "format": "json",
                "titles": term,
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
                        extract_text = page_info["extract"]
                        if len(extract_text) > 50:
                            wiki_summary = extract_text
                            break
            if wiki_summary:
                break

        # 위키백과 기본 설명 보완
        if not wiki_summary:
            wiki_summary = (
                f"{korean_name}(학명: {scientific_name})은(는) {order_name} {family_name}에 속하는 자생 곤충입니다.\n\n"
                f"• **서식 환경:** 주로 {active_months[0] if active_months else '여름철'} 국내 산지, 숲, 하천 변 등 자연환경에서 관찰됩니다.\n"
                f"• **생태적 특징:** 생태계 먹이사슬의 주요 구성원으로서 다양한 역할을 수행합니다."
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
