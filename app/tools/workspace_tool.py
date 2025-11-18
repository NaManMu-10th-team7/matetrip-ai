import httpx
from typing import List

from langchain_core.tools import tool

from app.common.config import nestJSConfig

BASE_URL = nestJSConfig.NESTJS_BACKEND_URL


def get_workspace_tools():
    """
    [워크스페이스 관련 도구 모음]
    """
    # recommend_nearby_places와 충돌로 인해 임시 주석
    # @tool
    # def search_places(keyword: str):
    #     """
    #     지역명과 찾고 싶은 장소 키워드를 입력받아 장소를 검색합니다.
    #     예시: '강남역 맛집', '성수동 카페', '제주도 공항 근처 편의점'

    #     [답변 작성 규칙]
    #     1. 이 도구의 실행 결과(JSON)에는 x, y 좌표가 포함되어 있습니다.
    #     2. 하지만 사용자에게 답변할 때는 **절대 좌표(x, y)나 URL, ID를 말하지 마세요.**
    #     3. 오직 **이름, 도로명 주소, 전화번호, 카테고리**만 사용하여 자연스럽게 요약해 주세요.
    #     """
    #     try:
    #         with httpx.Client() as client:
    #             # NestJS API 호출 (GET /places/search?keyword=...)
    #             response = client.get(
    #                 f"{BASE_URL}/workspace/search",
    #                 params={"keyword": keyword},
    #             )

    #             response.raise_for_status()

    #             # 검색 결과(JSON 리스트)를 문자열로 반환
    #             data = response.json()

    #             print(data)

    #             if not data:
    #                 return "검색 결과가 없습니다."

    #             # AI에게는 요약된 정보만 줘도 되지만,
    #             # 프론트엔드에는 전체 데이터(좌표 포함)가 tool_output으로 전달됨
    #             return str(data)

    #     except Exception as e:
    #         return f"검색 중 에러 발생: {str(e)}"

    @tool
    def find_place_id_by_name(place_name: str) -> str:
        """
        장소 이름을 사용하여 데이터베이스에서 해당 장소의 고유 ID(place_id)를 찾습니다.
        사용자가 장소 이름을 언급하며 리뷰 조회 등 추가 정보를 요청할 때, 다른 도구(get_place_reviews)를 사용하기 위해 필요한 place_id를 얻기 위한 중간 단계로 사용하세요.

        Args:
            place_name (str): ID를 찾고자 하는 장소의 이름입니다.

        Returns:
            가장 유사도가 높은 장소의 place_id(문자열) 또는 장소를 찾지 못한 경우 에러 메시지를 반환합니다.
        """
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"{BASE_URL}/places/search", params={"name": place_name}
                )
                response.raise_for_status()
                places = response.json()

                if not places:
                    return f"'{place_name}'에 해당하는 장소를 찾을 수 없습니다."
                return places["placeIds"][0] # 가장 유사한 첫 번째 결과의 ID를 반환
        except Exception as e:
            return f"장소 ID 조회 중 에러 발생: {str(e)}"

    @tool
    def get_place_reviews(place_id: str) -> List[str] | str:
        """
        장소의 고유 ID를 사용하여 해당 장소의 최신 리뷰 10개를 가져옵니다.
        사용자가 특정 장소에 대한 리뷰나 사람들의 반응, 후기 등이 궁금하다고 할 때 사용하세요.

        Args:
            place_id (str): 리뷰를 조회할 장소의 고유 ID입니다.

        [답변 작성 규칙]
        1. 이 도구의 실행 결과는 리뷰 텍스트 목록입니다.
        2. 사용자에게 답변할 때는 이 리뷰들을 자연스럽게 요약해서 전달해야 합니다.
        3. "리뷰를 요약해드릴게요" 와 같은 직접적인 언급보다는, "이 장소에 대해서는 대체로 ~한 반응들이 많네요." 와 같이 자연스러운 어투를 사용하세요.
        """
        try:
            with httpx.Client() as client:
                # NestJS API 호출 (GET /place/{place_id})
                response = client.get(
                    f"{BASE_URL}/place-user-reviews/place/{place_id}",
                )
                response.raise_for_status()
                reviews = response.json().get("data", [])
   
                if not reviews:
                    return "해당 장소에 대한 리뷰를 찾을 수 없습니다."

                # 리뷰 내용만 추출하여 리스트로 반환
                return [review.get("content", "") for review in reviews]
        except Exception as e:
            return f"리뷰 조회 중 에러 발생: {str(e)}"

    @tool
    def recommend_places_by_all_users(workspace_id: str):
        """
        워크스페이스(게시글)에 참여 중인 모든 사용자의 성향을 종합해 모두가 좋아할 만한 장소를 추천합니다.
        사용자가 '우리 모두', '다같이 갈만한', '참여 인원 모두' 등의 표현으로 장소 추천을 요청할 때 사용하세요.

        Args:
            workspace_id (str): 추천의 기준이 될 워크스페이스의 고유 ID입니다.

        [답변 작성 규칙]
        1. 이 도구의 실행 결과에는 기술적인 정보(ID, 좌표 등)가 포함될 수 있습니다.
        2. 하지만 사용자에게 답변할 때는 **절대 기술적인 정보를 말하지 마세요.**
        3. 오직 **이름, 주소, 카테고리** 등 사람이 읽을 수 있는 정보만 사용하여 자연스럽게 요약해 주세요.
        """
        try:
            with httpx.Client() as client:
                # NestJS API 호출 (GET /workspace/{workspace_id}/recommendations)
                response = client.get(
                    f"{BASE_URL}/workspace/{workspace_id}/recommendations",
                )
                response.raise_for_status()
                data = response.json()
                return data if data else "모두를 위한 추천 장소를 찾지 못했습니다."

        except Exception as e:
            return f"추천 장소 검색 중 에러 발생: {str(e)}"

    # return [search_places, recommend_places_by_all_users] # recommend_nearby_places와 충돌로 인해 임시 주석
    return [
        find_place_id_by_name,
        get_place_reviews,
        recommend_places_by_all_users,
    ]
