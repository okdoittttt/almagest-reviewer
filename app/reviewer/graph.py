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
    summarize_review
)


def create_review_graph() -> StateGraph:
    """
    코드 리뷰 LanGraph 그래프 생성

    그래프 흐름 (병렬 처리 버전):
    START
      ↓
    analyze_intent (PR 의도 분석)
      ↓
    classify_risk (위험도 분류)
      ↓
    review_all_files (모든 파일 병렬 리뷰)
      ↓
    summarize (최종 요약)
      ↓
    END

    Returns:
        컴파일된 StateGraph
    """
    logger.info("🏗️  LanGraph 리뷰 그래프 생성 중...")

    # 그래프 생성
    workflow = StateGraph(ReviewState)

    # 노드 추가
    workflow.add_node("analyze_intent", analyze_pr_intent)
    workflow.add_node("classify_risk", classify_risk)
    workflow.add_node("review_all_files", review_all_files)
    workflow.add_node("summarize", summarize_review)

    # 시작점 설정
    workflow.set_entry_point("analyze_intent")

    # 순차 엣지
    workflow.add_edge("analyze_intent", "classify_risk")
    workflow.add_edge("classify_risk", "review_all_files")
    workflow.add_edge("review_all_files", "summarize")
    workflow.add_edge("summarize", END)

    logger.info("✅ LanGraph 그래프 생성 완료 (병렬 처리)")

    return workflow


# 그래프 싱글톤 인스턴스
_compiled_graph = None


def get_review_graph():
    """
    컴파일된 리뷰 그래프 반환 (싱글톤)

    Returns:
        컴파일된 StateGraph
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
    """
    PR 리뷰 그래프 실행

    Args:
        pr_data: PRData 객체
        installation_id: Installation ID
        repo_owner: 리포지토리 소유자
        repo_name: 리포지토리 이름

    Returns:
        최종 ReviewState
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
