from pydantic import BaseModel, Field
from typing import List, Any, Optional

# --- 1. NestJS로부터 받을 데이터 (Input DTO) ---
class PlanGenerationRequest(BaseModel):
    """
    NestJS가 AI에게 계획 생성을 요청할 때 보낼 DTO
    """
    places: List[Any] = Field(description="장소 DTO 객체들의 리스트")
    start_date: str = Field(description="여행 시작일 (YYYY-MM-DD)")
    end_date: str = Field(description="여행 종료일 (YYYY-MM-DD)")

# --- 2. AI가 반환할 데이터 (Output DTOs) ---
# 이 모델들이 사용자님이 요청하신 JSON 구조입니다.
class RecommendedPOI(BaseModel):
    """
    개별 장소(POI)의 상세 정보 DTO
    """
    id: str = Field(description="원본 장소 ID (예 : rec_poi_123)")
    placeName: str
    address: str
    latitude: float
    longitude: float
    categoryName: str
    imageUrl: Optional[str] = None
    summary: str

class DailyRecommendation(BaseModel):
    """
    날짜별 일정 DTO
    """
    pois: List[RecommendedPOI] = Field(description="해당 날짜에 방문할 POI 리스트")

class PlanResponse(BaseModel):
    """
    AI가 반환할 최종 여행 계획 JSON 루트
    """
    recommendations: List[DailyRecommendation]