"""
LanGraph Review Graph 정의
"""
from langgraph.graph import StateGraph, END
from loguru import logger

from app.reviewer.state import ReviewState
from app.reviewer.nodes import (
    analyze_pr_intent,
    classify_risk,
    review_all_files,
    summarize_review,
    load_repo_skills,
    load_previous_review,
)

MAX_RETRIES = 2  # 최대 review_all_files 실행 횟수 (초기 1회 + 재시도 1회)


def route_by_risk(state: ReviewState) -> str:
    """위험도에 따라 다음 노드를 결정하는 라우팅 함수.

    LOW는 파일 리뷰를 스킵하고 바로 요약으로 이동하며,
    MEDIUM/HIGH는 전체 파일 리뷰를 진행합니다.

    Args:
        state: 현재 리뷰 상태. `risk_assessment.level` 값을 참조합니다.

    Returns:
        다음 노드 이름. ``"summarize"`` 또는 ``"review_all_files"``.
    """
    risk_level = state.get("risk_assessment", {}).get("level", "MEDIUM").upper()
    if risk_level == "LOW":
        logger.info("🟢 LOW 위험도 → 파일 리뷰 스킵, 바로 요약")
        return "summarize"
    logger.info(f"🔶 {risk_level} 위험도 → 전체 파일 리뷰 진행")
    return "review_all_files"


def should_retry(state: ReviewState) -> str:
    """summarize 이후 재시도 여부를 결정하는 라우팅 함수.

    Args:
        state: 현재 리뷰 상태. `needs_retry`와 `retry_count` 값을 참조합니다.

    Returns:
        다음 노드 이름. ``"review_all_files"`` 또는 ``END``.
    """
    needs_retry = state.get("needs_retry", False)
    retry_count = state.get("retry_count", 0)

    if needs_retry and retry_count < MAX_RETRIES:
        logger.info(f"🔄 재시도 필요 ({retry_count}/{MAX_RETRIES}) → 파일 재리뷰")
        return "review_all_files"

    logger.info("✅ 재시도 불필요 → 종료")
    return END


def create_review_graph() -> StateGraph:
    """코드 리뷰 LanGraph 그래프를 생성합니다.

    그래프 흐름::

        START
          ↓
        load_skills (저장소 Skills 로드)
          ↓
        load_previous_review (이전 리뷰 + 미해결 코멘트 로드)
          ↓
        analyze_intent (PR 의도 분석)
          ↓
        classify_risk (위험도 분류)
          ↓ (조건부)
        LOW → summarize
        MEDIUM/HIGH → review_all_files
          ↓
        summarize (최종 요약)
          ↓ (조건부)
        needs_retry=True → review_all_files (최대 MAX_RETRIES회)
        needs_retry=False → END

    Returns:
        노드와 엣지가 설정된 StateGraph (컴파일 전).
    """
    logger.info("🏗️  LanGraph 리뷰 그래프 생성 중...")

    workflow = StateGraph(ReviewState)

    # 노드 추가
    workflow.add_node("load_skills", load_repo_skills)
    workflow.add_node("load_previous_review", load_previous_review)
    workflow.add_node("analyze_intent", analyze_pr_intent)
    workflow.add_node("classify_risk", classify_risk)
    workflow.add_node("review_all_files", review_all_files)
    workflow.add_node("summarize", summarize_review)

    # 시작점 설정
    workflow.set_entry_point("load_skills")

    # 순차 엣지
    workflow.add_edge("load_skills", "load_previous_review")
    workflow.add_edge("load_previous_review", "analyze_intent")
    workflow.add_edge("analyze_intent", "classify_risk")

    # 조건부 엣지 1: 위험도에 따라 파일 리뷰 스킵 여부 결정
    workflow.add_conditional_edges(
        "classify_risk",
        route_by_risk,
        {
            "review_all_files": "review_all_files",
            "summarize": "summarize",
        }
    )

    workflow.add_edge("review_all_files", "summarize")

    # 조건부 엣지 2: summarize 후 재시도 여부 결정
    workflow.add_conditional_edges(
        "summarize",
        should_retry,
        {
            "review_all_files": "review_all_files",
            END: END,
        }
    )

    logger.info("✅ LanGraph 그래프 생성 완료 (risk 분기 + 재시도 루프)")

    return workflow


# 그래프 싱글톤 인스턴스
_compiled_graph = None


def get_review_graph():
    """컴파일된 리뷰 그래프를 반환합니다 (싱글톤).

    Returns:
        컴파일된 StateGraph 인스턴스.
    """
    global _compiled_graph

    if _compiled_graph is None:
        logger.info("📦 리뷰 그래프 컴파일 중...")
        workflow = create_review_graph()
        _compiled_graph = workflow.compile()
        logger.info("✅ 리뷰 그래프 컴파일 완료")

    return _compiled_graph


# 편의 함수: 그래프 실행
async def run_review(
    pr_data,
    installation_id: str,
    repo_owner: str,
    repo_name: str
) -> dict:
    """PR 리뷰 그래프를 실행합니다.

    Args:
        pr_data: PRData 객체.
        installation_id: GitHub App Installation ID.
        repo_owner: 리포지토리 소유자.
        repo_name: 리포지토리 이름.

    Returns:
        그래프 실행 완료 후의 최종 ReviewState.
    """
    from app.reviewer.state import create_initial_state

    logger.info(f"🚀 PR 리뷰 시작: {repo_owner}/{repo_name}")

    # 초기 상태 생성
    initial_state = create_initial_state(
        pr_data=pr_data,
        installation_id=installation_id,
        repo_owner=repo_owner,
        repo_name=repo_name
    )

    # 그래프 실행
    graph = get_review_graph()
    result = await graph.ainvoke(initial_state)

    logger.info("✅ PR 리뷰 완료")

    return result
