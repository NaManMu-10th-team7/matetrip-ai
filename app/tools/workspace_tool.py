import httpx
from langchain_core.tools import tool
from app.common.config import nestJSConfig

BASE_URL = nestJSConfig.NESTJS_BACKEND_URL



    @tool
    def get_my_profile():
        """현재 로그인한 사용자의 프로필 정보를 조회합니다."""
        try:
            with httpx.Client() as client:
                # 설정한 헤더(Authorization)를 달고 요청
                response = client.get(f"{BASE_URL}/users/me", headers=headers)
                response.raise_for_status()
                return str(response.json())
        except Exception as e:
            return f"API 호출 에러: {str(e)}"

    @tool
    def create_travel_plan(destination: str, days: int):
        """여행지(destination)와 기간(days)을 입력받아 여행 계획을 생성합니다."""
        payload = {"destination": destination, "days": days}
        try:
            with httpx.Client() as client:
                response = client.post(f"{BASE_URL}/plans", json=payload, headers=headers)
                response.raise_for_status()
                return f"생성 완료: {str(response.json())}"
        except Exception as e:
            return f"API 호출 에러: {str(e)}"

    return [get_my_profile, create_travel_plan]