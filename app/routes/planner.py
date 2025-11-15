import json

from fastapi import APIRouter

from app.core.llm import global_llm
from app.schemas.plan import PlanGenerationRequest, PlanResponse

from langchain_core.prompts import ChatPromptTemplate

router = APIRouter(prefix="/plan", tags=["Planner"])

# 1. 프롬프트 정의
# AI에게 주어진 장소 리스트 안에서만 사용해라 라고 강하게 지시
plan_prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a professional travel planner. Your task is to create a structured JSON itinerary."
        "You MUST follow these rules:\n"
        "1. Use ONLY the places provided in the <place_list>.\n"
        "2. **Logically group the places into daily plans** based on the trip duration ({start_date} to {end_date}). "
        "   Each object in the 'recommendations' array represents one day.\n"
        "3. **Crucially, you MUST generate a new, brief 'summary' for each place.**\n"
        "4. You MUST copy all other fields (id, placeName, address, latitude, longitude, etc.) "
        "   verbatim from the original data in the <place_list>.\n"
        "5. You MUST return your plan in the 'PlanResponse' JSON format. "
        "   (The 'DailyRecommendation' object *only* contains a 'pois' list)."
    )),
    ("human", (
        "Here are the recommended places (JSON format):\n"
        "<place_list>\n{places_json}\n</place_list>\n\n"
        "Create the itinerary for {start_date} to {end_date}."
    ))
])

# 2. LLM 체인 생성
# .with_structured_output()이 AI가 PlanResponse DTO에 맞춰 JSON을 생성하도록 강제
planner_chain = plan_prompt | global_llm.with_structured_output(PlanResponse)

# 3. 엔드포인트 생성
@router.post("/generate", response_model=PlanResponse)
async def generate_plan(request: PlanGenerationRequest):
    """
    NestJS로부터 장소 리스트와 날짜를 받아 여행 계획 JSON을 생성합니다.
    """
    try:
        # DTO 리스트를 AI가 읽기 쉽도록 JSON 문자열로 변환
        places_json = json.dumps(request.places, indent=2, ensure_ascii=False)

        # AI 호출
        plan_object: PlanResponse = planner_chain.invoke({
            "places_json": places_json,
            "start_date": request.start_date,
            "end_date": request.end_date
        })

        return plan_object
    except Exception as e:
        return {"error": str(e)}