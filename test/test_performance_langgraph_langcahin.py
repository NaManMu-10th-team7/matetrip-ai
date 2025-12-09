"""
LangChain vs LangGraph 성능 비교 테스트
"""

import asyncio
import time
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any
import httpx
from statistics import mean, stdev


# 테스트 설정
BASE_URL = "http://localhost:8000"
TIMEOUT = 120.0  # 각 요청당 타임아웃

# 테스트 시나리오: 3턴의 대화로 컨텍스트 누적 효과 확인
TEST_SCENARIOS = [
    {
        "name": "짧은 대화 (3턴)",
        "queries": [
            "서울 강남 맛집 추천해줘",
            "첫 번째 가게 전화번호 알려줘",
            "거기 근처 카페도 알려줘",
        ],
    },
    {
        "name": "중간 대화 (5턴)",
        "queries": [
            "부산 해운대 카페 추천해줘",
            "두 번째 장소 영업시간 알려줘",
            "거기 근처 식당도 찾아줘",
            "첫 번째 식당 주소 알려줘",
            "그 주변 주차장 있어?",
        ],
    },
]


class PerformanceTest:
    def __init__(self):
        self.results = {
            "test_timestamp": datetime.now().isoformat(),
            "langchain": {},
            "langgraph": {},
        }

    async def test_endpoint(
        self, endpoint: str, queries: List[str], session_id: str, scenario_name: str
    ) -> Dict[str, Any]:
        """단일 엔드포인트 테스트"""
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            results = {
                "scenario": scenario_name,
                "session_id": session_id,
                "turns": [],
                "total_time": 0,
                "avg_response_time": 0,
                "errors": [],
            }

            for i, query in enumerate(queries):
                turn_num = i + 1
                print(f"  턴 {turn_num}/{len(queries)}: {query[:30]}...")

                try:
                    start_time = time.perf_counter()

                    response = await client.post(
                        f"{BASE_URL}{endpoint}",
                        json={"query": query, "session_id": session_id},
                    )

                    end_time = time.perf_counter()
                    response_time = end_time - start_time

                    if response.status_code == 200:
                        data = response.json()
                        results["turns"].append(
                            {
                                "turn": turn_num,
                                "query": query,
                                "response_time": round(response_time, 4),
                                "response_preview": data.get("response", "")[:100],
                                "tool_count": len(data.get("tool_data", [])),
                            }
                        )
                    else:
                        results["errors"].append(
                            {
                                "turn": turn_num,
                                "error": f"HTTP {response.status_code}",
                                "detail": response.text[:200],
                            }
                        )

                except Exception as e:
                    results["errors"].append({"turn": turn_num, "error": str(e)})

                # 서버 부하 분산을 위한 짧은 대기
                await asyncio.sleep(0.5)

            # 통계 계산
            response_times = [t["response_time"] for t in results["turns"]]
            if response_times:
                results["total_time"] = round(sum(response_times), 4)
                results["avg_response_time"] = round(mean(response_times), 4)
                results["min_response_time"] = round(min(response_times), 4)
                results["max_response_time"] = round(max(response_times), 4)
                if len(response_times) > 1:
                    results["stdev_response_time"] = round(stdev(response_times), 4)

            return results

    async def run_comparison(self, scenario: Dict[str, Any]):
        """LangChain vs LangGraph 비교 실행"""
        scenario_name = scenario["name"]
        queries = scenario["queries"]

        print(f"\n{'='*60}")
        print(f"테스트 시나리오: {scenario_name}")
        print(f"{'='*60}")

        # 각 엔드포인트에 대해 독립적인 세션 ID 사용
        langchain_session = f"test_langchain_{uuid.uuid4().hex[:8]}"
        langgraph_session = f"test_langgraph_{uuid.uuid4().hex[:8]}"

        # LangChain 테스트
        print(f"\n[LangChain] /chat 엔드포인트 테스트 중...")
        langchain_result = await self.test_endpoint(
            "/chat", queries, langchain_session, scenario_name
        )

        # 서버 안정화 대기
        await asyncio.sleep(2)

        # LangGraph 테스트
        print(f"\n[LangGraph] /chat/v2 엔드포인트 테스트 중...")
        langgraph_result = await self.test_endpoint(
            "/chat/v2", queries, langgraph_session, scenario_name
        )

        # 결과 저장
        self.results["langchain"][scenario_name] = langchain_result
        self.results["langgraph"][scenario_name] = langgraph_result

    async def run_all_tests(self):
        """모든 시나리오 테스트 실행"""
        for scenario in TEST_SCENARIOS:
            try:
                await self.run_comparison(scenario)
            except Exception as e:
                print(f"❌ 시나리오 '{scenario['name']}' 실패: {e}")

        # 결과 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"performance_results_{timestamp}.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 결과가 {output_file}에 저장되었습니다.")
        return output_file

    def generate_report(self, output_file: str):
        """성능 분석 리포트 생성"""
        print(f"\n{'='*60}")
        print("성능 비교 분석 리포트")
        print(f"{'='*60}\n")

        for scenario_name in self.results["langchain"].keys():
            lc_result = self.results["langchain"][scenario_name]
            lg_result = self.results["langgraph"][scenario_name]

            print(f"\n[시나리오: {scenario_name}]")
            print(f"{'-'*60}")

            # 응답 시간 비교
            if lc_result.get("avg_response_time") and lg_result.get(
                "avg_response_time"
            ):
                lc_avg = lc_result["avg_response_time"]
                lg_avg = lg_result["avg_response_time"]
                improvement = ((lc_avg - lg_avg) / lc_avg) * 100

                print(f"\n📈 평균 응답 시간:")
                print(f"  LangChain:  {lc_avg:.4f}초")
                print(f"  LangGraph:  {lg_avg:.4f}초")
                print(
                    f"  개선율:     {improvement:+.2f}% {'🚀' if improvement > 0 else '📉'}"
                )

                print(f"\n⏱️  총 처리 시간:")
                print(f"  LangChain:  {lc_result['total_time']:.4f}초")
                print(f"  LangGraph:  {lg_result['total_time']:.4f}초")

                # 턴별 비교
                print(f"\n📋 턴별 응답 시간 비교:")
                print(f"  {'턴':<5} {'LangChain':<12} {'LangGraph':<12} {'차이':<10}")
                print(f"  {'-'*5} {'-'*12} {'-'*12} {'-'*10}")

                for i in range(len(lc_result["turns"])):
                    lc_time = lc_result["turns"][i]["response_time"]
                    lg_time = lg_result["turns"][i]["response_time"]
                    diff = lc_time - lg_time
                    print(f"  {i+1:<5} {lc_time:<12.4f} {lg_time:<12.4f} {diff:+.4f}초")

            # 에러 확인
            if lc_result.get("errors") or lg_result.get("errors"):
                print(f"\n⚠️  에러:")
                if lc_result.get("errors"):
                    print(f"  LangChain: {len(lc_result['errors'])}건")
                if lg_result.get("errors"):
                    print(f"  LangGraph: {len(lg_result['errors'])}건")

        # 전체 요약
        print(f"\n{'='*60}")
        print("📊 전체 요약")
        print(f"{'='*60}\n")

        all_lc_times = []
        all_lg_times = []

        for scenario_name in self.results["langchain"].keys():
            lc_result = self.results["langchain"][scenario_name]
            lg_result = self.results["langgraph"][scenario_name]

            if lc_result.get("turns"):
                all_lc_times.extend([t["response_time"] for t in lc_result["turns"]])
            if lg_result.get("turns"):
                all_lg_times.extend([t["response_time"] for t in lg_result["turns"]])

        if all_lc_times and all_lg_times:
            lc_overall_avg = mean(all_lc_times)
            lg_overall_avg = mean(all_lg_times)
            overall_improvement = (
                (lc_overall_avg - lg_overall_avg) / lc_overall_avg
            ) * 100

            print(f"전체 평균 응답 시간:")
            print(f"  LangChain:  {lc_overall_avg:.4f}초")
            print(f"  LangGraph:  {lg_overall_avg:.4f}초")
            print(
                f"  전체 개선율: {overall_improvement:+.2f}% {'🎉' if overall_improvement > 0 else ''}"
            )

            print(f"\n포트폴리오 작성용 요약:")
            print(f"{'-'*60}")
            if overall_improvement > 0:
                print(
                    f"✅ LangGraph 도입으로 평균 응답 시간 {abs(overall_improvement):.1f}% 개선"
                )
                print(f"   - 기존(LangChain): {lc_overall_avg:.2f}초")
                print(f"   - 개선(LangGraph): {lg_overall_avg:.2f}초")
            else:
                print(f"⚠️ 응답 시간 차이: {abs(overall_improvement):.1f}%")
                print(f"   - 성능 차이가 크지 않음 (두 방식 모두 유사한 성능)")

        print(f"\n상세 결과는 {output_file}을 참고하세요.\n")


async def main():
    """메인 실행 함수"""
    print("🚀 LangChain vs LangGraph 성능 비교 테스트 시작\n")
    print(f"테스트 대상:")
    print(f"  - LangChain: {BASE_URL}/chat")
    print(f"  - LangGraph: {BASE_URL}/chat/v2")
    print(f"\n테스트 시나리오: {len(TEST_SCENARIOS)}개")
    for scenario in TEST_SCENARIOS:
        print(f"  - {scenario['name']}: {len(scenario['queries'])}턴")

    # 서버 확인
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/")
            if response.status_code != 200:
                print(f"\n❌ 서버 응답 오류: HTTP {response.status_code}")
                return
    except Exception as e:
        print(f"\n❌ 서버에 연결할 수 없습니다: {e}")
        print(f"서버를 먼저 실행해주세요: uvicorn main:app --reload")
        return

    print("\n✅ 서버 연결 확인 완료. 테스트를 시작합니다...\n")

    test = PerformanceTest()
    output_file = await test.run_all_tests()
    test.generate_report(output_file)


if __name__ == "__main__":
    asyncio.run(main())
